"""
Local Auto-AVSR (visual speech recognition) inference.

Replicates the AD1TEYA HF Space InferencePipeline but:
  - runs locally (CPU or MPS), no GPU Space dependency
  - uses the bundled MediaPipe detector (CPU)
  - exposes N-BEST hypotheses + scores (for downstream LLM correction)

Pipeline: read_video -> mediapipe 4-keypoint detect -> affine-align + mouth
crop (96x96) -> CenterCrop(88)+grayscale+normalize -> conformer + beam search.
"""
import os
import argparse
import time
from pathlib import Path

import torch
import torchvision

from .datamodule.transforms import VideoTransform, TextTransform
from .lightning import get_beam_search_decoder
from .espnet.nets.pytorch_backend.e2e_asr_conformer import E2E

CKPT = str(
    Path(__file__).resolve().parents[4]
    / "models"
    / "aditeya-vsr"
    / "pytorch_model.pt"
)


class LocalVSR:
    def __init__(self, ckpt_path=CKPT, device="cpu", enhance=False,
                 detector="mediapipe", det_device="cpu"):
        self.device = torch.device(device)
        self.enhance = enhance  # CLAHE contrast enhancement on luminance
        self.detector = detector
        if detector == "retinaface":
            try:
                from open_altergo_engine.preparation.detectors.retinaface.detector import LandmarksDetector
                from open_altergo_engine.preparation.detectors.retinaface.video_process import VideoProcess
                self.landmarks_detector = LandmarksDetector(device=det_device,
                                                            model_name="mobilenet0.25")
            except Exception as e:
                print(f"[LocalVSR] retinaface unavailable ({e}); "
                      f"falling back to mediapipe")
                detector = "mediapipe"
                self.detector = "mediapipe"
        if detector != "retinaface":
            from open_altergo_engine.preparation.detectors.mediapipe.detector import LandmarksDetector
            from open_altergo_engine.preparation.detectors.mediapipe.video_process import VideoProcess
            self.landmarks_detector = LandmarksDetector()
        self.video_process = VideoProcess(convert_gray=False)
        self.video_transform = VideoTransform(subset="test")

        self.text_transform = TextTransform()
        self.token_list = self.text_transform.token_list

        self.model = E2E(len(self.token_list), "video", ctc_weight=0.1)
        if not os.path.isfile(ckpt_path):
            from huggingface_hub import hf_hub_download
            # prefer our self-contained public mirror; fall back to upstream
            for repo in ("aaahmet/silent-lip-reader-model", "AD1TEYA/lip-reading-model"):
                try:
                    ckpt_path = hf_hub_download(repo_id=repo, filename="pytorch_model.pt")
                    break
                except Exception:
                    continue
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        self.model.load_state_dict(ckpt)
        self.model = self.model.to(self.device).eval()

        self.beam_search = get_beam_search_decoder(self.model, self.token_list)
        # move beam-search scorers to device
        try:
            self.beam_search = self.beam_search.to(self.device)
        except Exception:
            pass

    def load_video(self, path):
        import cv2
        import numpy as np
        cap = cv2.VideoCapture(path)
        frames = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            if self.enhance:
                lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
                clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
                lab[:, :, 0] = clahe.apply(lab[:, :, 0])
                rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            frames.append(rgb)
        cap.release()
        return np.stack(frames)  # T,H,W,3 uint8 RGB

    def set_decoder(self, beam_size=40, ctc_weight=0.1, penalty=0.0, lm_weight=0.0):
        """Rebuild the beam-search decoder with custom params (for sweeps)."""
        self.beam_search = get_beam_search_decoder(
            self.model, self.token_list, penalty=penalty,
            ctc_weight=ctc_weight, lm_weight=lm_weight, beam_size=beam_size)
        try:
            self.beam_search = self.beam_search.to(self.device)
        except Exception:
            pass

    def crop_sequence(self, path):
        """Whole video -> aligned mouth-ROI uint8 sequence (T,96,96,3)."""
        video = self.load_video(path)               # T,H,W,3 uint8 RGB
        landmarks = self.landmarks_detector(video)
        roi = self.video_process(video, landmarks)  # T,96,96,3 uint8
        return roi

    def roi_to_tensor(self, roi):
        """(T,96,96,3) uint8 -> (T,1,88,88) normalized tensor on device."""
        import numpy as np
        t = torch.tensor(np.asarray(roi)).permute(0, 3, 1, 2)  # T,3,96,96
        t = self.video_transform(t)                            # T,1,88,88
        return t.to(self.device)

    def preprocess(self, path):
        return self.roi_to_tensor(self.crop_sequence(path))

    @torch.no_grad()
    def transcribe_tensor(self, sample, nbest=5):
        """Run the conformer + beam search on a preprocessed (T,1,88,88) tensor."""
        x = self.model.frontend(sample.unsqueeze(0))
        x = self.model.proj_encoder(x)
        enc_feat, _ = self.model.encoder(x, None)
        enc_feat = enc_feat.squeeze(0)
        hyps = self.beam_search(enc_feat)
        out = []
        for h in hyps[: min(len(hyps), nbest)]:
            d = h.asdict()
            ids = torch.tensor(list(map(int, d["yseq"][1:])))
            text = self.text_transform.post_process(ids).replace("<eos>", "").strip()
            out.append({"text": text, "score": float(d["score"])})
        return out

    @torch.no_grad()
    def transcribe(self, path, nbest=5):
        return self.transcribe_tensor(self.preprocess(path), nbest=nbest)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--ckpt-path", default=CKPT)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--nbest", type=int, default=5)
    a = ap.parse_args()

    t0 = time.time()
    vsr = LocalVSR(ckpt_path=a.ckpt_path, device=a.device)
    t1 = time.time()
    hyps = vsr.transcribe(a.video, nbest=a.nbest)
    t2 = time.time()
    print(f"[load {t1-t0:.1f}s | infer {t2-t1:.1f}s | device {a.device}]")
    for i, h in enumerate(hyps):
        print(f"  {i+1}. ({h['score']:.2f}) {h['text']}")
