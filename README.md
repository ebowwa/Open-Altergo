---
title: Open Altergo
emoji: 👄
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 6.15.2
python_version: "3.11"
app_file: app.py
pinned: false
license: mit
short_description: Extensible silent-speech inference and personalization
tags:
  - lip-reading
  - visual-speech-recognition
  - silent-speech
  - gradio
---

# Open-Altergo

Open-Altergo is an extensible silent-speech system: it reads visible mouth
movement from video, returns text, and can be personalized to a speaker. The
repository separates the reusable API, model engine, interfaces, training
workflows, and cloud provisioning so future Swift, HTTP, or desktop interfaces
do not depend on Gradio.

Audio is stripped before inference. The current model is Auto-AVSR and the
current browser interface is Gradio.

## Repository map

```text
apps/
└── gradio/                    Gradio UI and its dependencies
packages/
└── silent_speech/             Interface-neutral service package
training/                      Dataset preparation and fine-tuning commands
cloud/
├── engine/                    Installable Auto-AVSR engine package
└── modal/                     Modal provisioning and job definitions
docs/
├── interface-architecture.md
├── modal-finetuning.md
├── RESEARCH_LOG.md
└── Silent-Lip-Reader-README.md
app.py                         Hugging Face compatibility launcher
```

The dependency direction is deliberate:

```text
Gradio / future Swift bridge ──► silent_speech ──► engine
training workflows ─────────────────────────────► engine
Modal ────────────────────────► training workflows
```

## Run the Gradio application

Python 3.11 and `ffmpeg` are recommended.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The first inference downloads the public Auto-AVSR checkpoint if no local
checkpoint is configured.

## Use the core without Gradio

```bash
pip install -r requirements-core.txt
```

```python
from silent_speech import RuntimeConfig, SilentSpeechService

service = SilentSpeechService(RuntimeConfig(device="cpu"))
result = service.transcribe("sample.mp4")
print(result["transcript"])
```

Set `LIPREAD_CKPT` to use a personalized checkpoint.

## Train on generic compute

The training code is not tied to Modal. On a machine with a CUDA GPU:

```bash
python training/prepare_dataset.py \
  --manifest datasets/me/manifest.csv \
  --output-dir datasets/me/processed \
  --dataset-name me

python training/train_personal.py \
  --root-dir datasets/me/processed \
  --output-dir runs/me-v1 \
  --train-file me_train.csv \
  --val-file me_val.csv
```

See [Modal fine-tuning](docs/modal-finetuning.md) for provisioned A10 training,
persistent checkpoints, and Doppler-based secret injection.

## Status and provenance

The repository contains a complete preprocessing and personalized fine-tuning
workflow, but it does not yet include a project-specific Modal run log or
evaluated personalized checkpoint. Treat personalized quality claims as
unverified until held-out WER is recorded.

The original demo, pipeline work, evaluation, and research were created by
[Ahmet Dedeler](https://ahmetdedeler.com) around the open Auto-AVSR model.
See the archived [Silent Lip Reader README](docs/Silent-Lip-Reader-README.md)
and [research log](docs/RESEARCH_LOG.md) for history, limitations, and credits.

## Security

This is a public repository. Do not commit recordings, datasets, checkpoints,
API keys, Modal credentials, Doppler local state, or `.env` files. Use Doppler
or your compute provider's secret manager to inject credentials at runtime.

MIT licensed.
