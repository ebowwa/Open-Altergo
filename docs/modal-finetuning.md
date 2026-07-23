# Personalized fine-tuning on Modal

This workflow adapts the pretrained Auto-AVSR checkpoint to one person's mouth,
articulation, camera, and vocabulary. Modal provisions compute; the provider-
independent training implementation remains in `training/` and
`open_altergo_engine`.

The default strategy freezes the visual frontend and most of the 12-block
Conformer. It updates the final two Conformer blocks, projection, Transformer
decoder, and CTC head.

## 1. Install the Modal control-plane dependency

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r cloud/modal/requirements.txt
```

Open-Altergo does not store Modal credentials. If Modal tokens are managed in
Doppler, expose `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` only to each command:

```bash
doppler run -- modal profile current
```

Interactive `modal setup` also works, but its generated credentials must remain
outside the repository.

The app creates three persistent Volumes:

- `silent-lip-reader-data` for recordings and processed mouth crops
- `silent-lip-reader-runs` for checkpoints and exported models
- `silent-lip-reader-hf-cache` for checkpoint and tokenizer downloads

## 2. Record a prompted dataset

Use at least three recording sessions and keep sentences disjoint across train,
validation, and test splits. A practical starting point is 300 unique prompts,
recorded once normally and once while mouthing silently.

```text
datasets/elijah/
├── manifest.csv
└── clips/
    ├── session01-0001.mp4
    └── ...
```

`manifest.csv` contains `id,video,text,split`:

```csv
id,video,text,split
session01-0001,clips/session01-0001.mp4,hey how is everyone today,train
session02-0001,clips/session02-0001.mp4,can you tell me the latest with the task,val
session03-0001,clips/session03-0001.mp4,please send the update when it is ready,test
```

## 3. Upload and preprocess

```bash
doppler run -- modal volume create silent-lip-reader-data
doppler run -- modal volume put \
  silent-lip-reader-data ./datasets/elijah /elijah
doppler run -- modal run cloud/modal/app.py::prepare \
  --dataset-name elijah
```

Preprocessing strips audio, normalizes to 25 fps, aligns the face, writes 96x96
mouth-only videos, uppercases text for the released SentencePiece vocabulary,
and emits Auto-AVSR label files. Add `--flip` only for mirrored source files.

## 4. Fine-tune

```bash
doppler run -- modal run --detach cloud/modal/app.py::train \
  --dataset-name elijah \
  --run-name elijah-v1 \
  --max-epochs 30
```

The A10 job writes `last.ckpt` and resumes it when the same run name is launched
again. Available strategies are:

- `decoder`: decoder and CTC head only
- `encoder-decoder`: projection, last N Conformer blocks, decoder, and CTC
- `full`: every parameter; risky for a small personal dataset

## 5. Download and evaluate

```bash
mkdir -p models
doppler run -- modal volume get silent-lip-reader-runs \
  /elijah-v1/personalized_model.pt \
  ./models/elijah-v1.pt

python -m open_altergo_engine.local_infer sample.mp4 \
  --ckpt-path ./models/elijah-v1.pt
```

Or launch Gradio with the checkpoint:

```bash
LIPREAD_CKPT=./models/elijah-v1.pt python app.py
```

Always report raw visual-only WER on unseen sentences before adding an LLM
correction layer. The exported checkpoint is speaker-specific.
