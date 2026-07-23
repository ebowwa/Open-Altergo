"""
Silent-friendly lip-reading pipeline.

Processes the whole video once into an aligned mouth-ROI sequence, derives a
lip-MOTION signal (no audio needed), segments it into utterances, and runs the
Auto-AVSR model on each segment. This makes the system work on fully silent
recordings (the in-browser webcam case) where audio VAD is impossible.
"""
import os
import sys
import subprocess
import tempfile
import numpy as np

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from local_infer import LocalVSR


def normalize_video(path, hflip=False, fps=25, max_seconds=None):
    """Re-encode to fixed fps, optional un-mirror, strip audio, cap length.
    Returns temp path."""
    out = tempfile.mktemp(suffix=".mp4")
    vf = (["hflip"] if hflip else []) + [f"fps={fps}"]
    cmd = ["ffmpeg", "-y"]
    if max_seconds:
        cmd += ["-t", str(max_seconds)]
    cmd += ["-i", path, "-vf", ",".join(vf), "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-an", out]
    subprocess.run(cmd, capture_output=True)
    return out


def lip_motion(roi):
    """(T,96,96,3) uint8 -> per-frame motion energy (T,)."""
    g = roi.astype(np.float32).mean(axis=3)            # T,96,96 grayscale
    # focus on the lower-center mouth region to reduce head-motion noise
    g = g[:, 40:88, 24:72]
    diff = np.abs(np.diff(g, axis=0)).mean(axis=(1, 2))  # T-1
    motion = np.concatenate([[diff[0] if len(diff) else 0.0], diff])
    return motion


def smooth(x, k=3):
    if len(x) < k:
        return x
    ker = np.ones(k) / k
    return np.convolve(x, ker, mode="same")


def segment_motion(motion, fps=25, thr_ratio=0.35, min_speech=0.50,
                   min_gap=0.55, pad=0.16):
    """Return list of (start_frame, end_frame) speech segments from motion.
    Tuned for SENTENCE-level splits: merge across intra-word mouth-closures,
    only break on real ~0.5s+ pauses between utterances."""
    m = smooth(motion, 5)
    if m.max() <= 1e-6:
        return [(0, len(m))]
    # adaptive threshold between the quiet floor and active level
    floor = np.percentile(m, 20)
    peak = np.percentile(m, 90)
    thr = floor + thr_ratio * (peak - floor)
    active = m > thr

    # collect runs of active frames
    segs = []
    i = 0
    T = len(active)
    while i < T:
        if active[i]:
            j = i
            while j < T and active[j]:
                j += 1
            segs.append([i, j])
            i = j
        else:
            i += 1
    if not segs:
        return [(0, T)]
    # merge segments separated by a short gap
    gap_f = int(min_gap * fps)
    merged = [segs[0]]
    for s in segs[1:]:
        if s[0] - merged[-1][1] <= gap_f:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    # pad + min-duration filter
    pad_f = int(pad * fps)
    min_f = int(min_speech * fps)
    out = []
    for a, b in merged:
        a = max(0, a - pad_f)
        b = min(T, b + pad_f)
        if b - a >= min_f:
            out.append((a, b))
    return out or [(0, T)]


class LipReader:
    def __init__(self, device="cpu", detector="retinaface", enhance=True,
                 ckpt_path=None):
        kwargs = {}
        if ckpt_path:
            kwargs["ckpt_path"] = ckpt_path
        self.vsr = LocalVSR(device=device, enhance=enhance, detector=detector,
                            det_device="cpu", **kwargs)
        self.fps = 25

    def transcribe(self, path, nbest=5, hflip=False, max_seconds=40):
        norm = normalize_video(path, hflip=hflip, fps=self.fps,
                               max_seconds=max_seconds)
        try:
            return self._transcribe_norm(norm, nbest=nbest)
        finally:
            try:
                os.remove(norm)
            except OSError:
                pass

    def _mean_score(self, out):
        """Confidence proxy: frame-weighted mean of top-1 beam scores."""
        num = den = 0.0
        for r in out["segments"]:
            if not r["nbest"]:
                continue
            n = r["seg_frames"][1] - r["seg_frames"][0]
            num += r["nbest"][0]["score"] * n
            den += n
        return (num / den) if den else -1e9

    def transcribe_auto(self, path, nbest=5, max_seconds=40):
        """Try both orientations, keep the higher-confidence one. Removes the
        'is the webcam mirrored?' guesswork."""
        best = None
        for hf in (False, True):
            out = self.transcribe(path, nbest=nbest, hflip=hf,
                                  max_seconds=max_seconds)
            out["hflip"] = hf
            out["score"] = self._mean_score(out)
            if best is None or out["score"] > best["score"]:
                best = out
        return best

    def _transcribe_norm(self, path, nbest=5):
        try:
            roi = self.vsr.crop_sequence(path)      # T,96,96,3
        except Exception:
            # mediapipe/retinaface raise if no face is found in any frame
            return {"segments": [], "transcript": "", "n_segments": 0,
                    "no_face": True}
        tensor = self.vsr.roi_to_tensor(roi)        # T,1,88,88
        motion = lip_motion(roi)
        segs = segment_motion(motion, fps=self.fps)
        # whole-clip fallback for very short recordings (<=4s -> 1 utterance)
        if tensor.shape[0] <= int(4.0 * self.fps) and len(segs) > 1:
            segs = [(0, tensor.shape[0])]
        results = []
        for (a, b) in segs:
            sub = tensor[a:b]
            if sub.shape[0] < 4:
                continue
            hyps = self.vsr.transcribe_tensor(sub, nbest=nbest)
            results.append({"seg_frames": [a, b],
                            "seg_time": [a / self.fps, b / self.fps],
                            "text": hyps[0]["text"].lower().strip(),
                            "nbest": hyps})
        full = " ".join(r["text"] for r in results)
        return {"segments": results, "transcript": full,
                "n_segments": len(segs)}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--detector", default="retinaface")
    ap.add_argument("--hflip", action="store_true", help="un-mirror (Photo Booth/selfie)")
    a = ap.parse_args()
    lr = LipReader(device=a.device, detector=a.detector)
    out = lr.transcribe(a.video, hflip=a.hflip)
    for r in out["segments"]:
        t = r["seg_time"]
        print(f"  [{t[0]:5.1f}-{t[1]:5.1f}s] {r['text']}")
    print("\nTRANSCRIPT:", out["transcript"])
