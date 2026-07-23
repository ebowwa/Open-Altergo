"""Convert prompted full-face videos into an Auto-AVSR training dataset.

Input is a CSV with ``id,video,text,split`` columns. Video paths are resolved
relative to the manifest. Output videos contain aligned 96x96 mouth crops at
25 fps; labels use the format expected by ``open_altergo_engine.datamodule``.
"""

import argparse
import csv
import json
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path


VALID_SPLITS = {"train", "val", "test"}


def _safe_component(value, field):
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip(".-")
    if not cleaned:
        raise ValueError(f"{field} must contain at least one letter or number")
    return cleaned


def _normalize_video(source, flip=False, max_seconds=16.0):
    handle = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    handle.close()
    destination = Path(handle.name)
    filters = ["hflip"] if flip else []
    filters.append("fps=25")
    command = ["ffmpeg", "-v", "error", "-y", "-i", str(source)]
    if max_seconds:
        command.extend(["-t", str(max_seconds)])
    command.extend(
        [
            "-vf",
            ",".join(filters),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(destination),
        ]
    )
    subprocess.run(command, check=True)
    return destination


def _load_rgb_frames(path):
    import cv2
    import numpy as np

    capture = cv2.VideoCapture(str(path))
    frames = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        capture.release()
    if not frames:
        raise ValueError(f"No frames could be decoded from {path}")
    return np.stack(frames)


def _write_roi_video(path, frames, fps=25.0):
    import cv2

    path.parent.mkdir(parents=True, exist_ok=True)
    height, width = frames.shape[1:3]
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
        True,
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer for {path}")
    try:
        for frame in frames:
            writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    finally:
        writer.release()


def _load_manifest(path):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"video", "text", "split"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Manifest is missing columns: {', '.join(sorted(missing))}"
            )
        return list(reader)


def prepare_dataset(
    manifest,
    output_dir,
    dataset_name,
    detector="mediapipe",
    flip=False,
    max_seconds=16.0,
    skip_errors=False,
):
    from open_altergo_engine.datamodule.transforms import TextTransform

    manifest = Path(manifest).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    dataset_name = _safe_component(dataset_name, "dataset_name")
    rows = _load_manifest(manifest)
    if not rows:
        raise ValueError("Manifest contains no examples")

    if detector == "mediapipe":
        from open_altergo_engine.preparation.detectors.mediapipe.detector import (
            LandmarksDetector,
        )
        from open_altergo_engine.preparation.detectors.mediapipe.video_process import (
            VideoProcess,
        )
    else:
        from open_altergo_engine.preparation.detectors.retinaface.detector import (
            LandmarksDetector,
        )
        from open_altergo_engine.preparation.detectors.retinaface.video_process import (
            VideoProcess,
        )

    landmarks_detector = LandmarksDetector()
    video_process = VideoProcess(convert_gray=False)
    text_transform = TextTransform()

    video_rel_dir = Path(f"{dataset_name}_video_seg24s")
    video_dir = output_dir / dataset_name / video_rel_dir
    labels_dir = output_dir / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)

    labels = defaultdict(list)
    metadata = []
    failures = []
    used_ids = set()

    for index, row in enumerate(rows):
        split = row["split"].strip().lower()
        if split not in VALID_SPLITS:
            raise ValueError(
                f"Row {index + 2} has split={split!r}; expected train, val, or test"
            )
        text = " ".join(row["text"].strip().split())
        if not text:
            raise ValueError(f"Row {index + 2} has an empty transcript")

        source = Path(row["video"].strip()).expanduser()
        if not source.is_absolute():
            source = manifest.parent / source
        source = source.resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Input video not found: {source}")

        sample_id = row.get("id", "").strip() or f"{index:05d}-{source.stem}"
        sample_id = _safe_component(sample_id, "id")
        if sample_id in used_ids:
            raise ValueError(f"Duplicate sample id: {sample_id}")
        used_ids.add(sample_id)
        destination = video_dir / f"{sample_id}.mp4"

        normalized = None
        try:
            normalized = _normalize_video(
                source,
                flip=flip,
                max_seconds=max_seconds,
            )
            frames = _load_rgb_frames(normalized)
            landmarks = landmarks_detector(frames)
            roi = video_process(frames, landmarks)
            if roi is None or len(roi) < 4:
                raise ValueError("Fewer than four usable mouth frames")
            _write_roi_video(destination, roi)

            # The released Auto-AVSR SentencePiece vocabulary is uppercase.
            # Tokenizing lowercase prompts silently maps most words to <unk>,
            # so normalize here while preserving the user's text in metadata.
            token_ids = text_transform.tokenize(text.upper()).tolist()
            token_string = " ".join(str(token) for token in token_ids)
            rel_path = (video_rel_dir / destination.name).as_posix()
            labels[split].append(
                f"{dataset_name},{rel_path},{len(roi)},{token_string}"
            )
            metadata.append(
                {
                    "id": sample_id,
                    "source": str(source),
                    "processed": str(destination),
                    "text": text,
                    "split": split,
                    "frames": len(roi),
                }
            )
            print(f"[{index + 1}/{len(rows)}] {sample_id}: {len(roi)} frames")
        except Exception as error:
            failure = {"id": sample_id, "source": str(source), "error": str(error)}
            failures.append(failure)
            if not skip_errors:
                raise
            print(f"Skipping {sample_id}: {error}", file=sys.stderr)
        finally:
            if normalized:
                normalized.unlink(missing_ok=True)

    for split in sorted(VALID_SPLITS):
        if labels[split]:
            label_path = labels_dir / f"{dataset_name}_{split}.csv"
            label_path.write_text("\n".join(labels[split]) + "\n", encoding="utf-8")

    summary = {
        "dataset_name": dataset_name,
        "manifest": str(manifest),
        "output_dir": str(output_dir),
        "examples": len(metadata),
        "failures": failures,
        "splits": {split: len(labels[split]) for split in sorted(VALID_SPLITS)},
    }
    (output_dir / "metadata.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in metadata),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--detector", choices=["mediapipe", "retinaface"], default="mediapipe")
    parser.add_argument("--flip", action="store_true")
    parser.add_argument("--max-seconds", type=float, default=16.0)
    parser.add_argument("--skip-errors", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    result = prepare_dataset(
        manifest=args.manifest,
        output_dir=args.output_dir,
        dataset_name=args.dataset_name,
        detector=args.detector,
        flip=args.flip,
        max_seconds=args.max_seconds,
        skip_errors=args.skip_errors,
    )
    print(json.dumps(result, indent=2))
