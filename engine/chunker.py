"""
Audio-VAD utterance chunker.

Uses the audio track ONLY for *timing* (where speech starts/stops), never content,
so the downstream transcription remains a pure lip-read. Returns utterance segments
(start, end) in seconds. Later this can be swapped for a visual (lip-motion) VAD for
a truly silent pipeline.
"""
import re
import subprocess


def detect_silences(path, noise_db=-30, min_sil=0.5):
    cmd = ["ffmpeg", "-i", path, "-af",
           f"silencedetect=noise={noise_db}dB:d={min_sil}", "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]
    return starts, ends


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True).stdout.strip()
    return float(out)


def speech_segments(path, noise_db=-30, min_sil=0.5, merge_gap=0.4,
                    pad=0.12, min_dur=0.30):
    """Invert silence -> speech segments, merge close ones, pad, drop tiny."""
    dur = duration(path)
    starts, ends = detect_silences(path, noise_db, min_sil)

    # Build silence intervals
    sil = []
    s_iter = list(starts)
    e_iter = list(ends)
    # pair them; silence may start at 0 or run to end
    i = j = 0
    # Construct ordered silence intervals
    pts = []
    for s in starts:
        pts.append(("s", s))
    for e in ends:
        pts.append(("e", e))
    pts.sort(key=lambda x: x[1])
    cur = None
    for kind, t in pts:
        if kind == "s":
            cur = t
        elif kind == "e":
            st = cur if cur is not None else 0.0
            sil.append((st, t))
            cur = None
    if cur is not None:  # trailing silence to end
        sil.append((cur, dur))

    # Invert to speech
    speech = []
    prev = 0.0
    for (a, b) in sil:
        if a - prev > 1e-3:
            speech.append([prev, a])
        prev = b
    if dur - prev > 1e-3:
        speech.append([prev, dur])

    # Merge close, pad, filter
    merged = []
    for seg in speech:
        if merged and seg[0] - merged[-1][1] <= merge_gap:
            merged[-1][1] = seg[1]
        else:
            merged.append(seg)
    out = []
    for a, b in merged:
        a = max(0.0, a - pad)
        b = min(dur, b + pad)
        if b - a >= min_dur:
            out.append((round(a, 3), round(b, 3)))
    return out


if __name__ == "__main__":
    import sys
    for seg in speech_segments(sys.argv[1]):
        print(f"{seg[0]:7.2f} -> {seg[1]:7.2f}  ({seg[1]-seg[0]:.2f}s)")
