# Personalized fine-tuning on Modal

This workflow adapts the pretrained Auto-AVSR checkpoint to one person's mouth,
articulation, camera, and vocabulary. It trains from exact prompted text and
video; audio is not required.

Modal is the cloud provisioning and execution layer here: it builds the image,
allocates the A10 GPU, mounts persistent Volumes, retries interrupted work, and
runs detached jobs. `train_personal.py` and the bundled Auto-AVSR/Lightning code
contain the model, loss, optimizer, scheduler, and fine-tuning logic.

The default strategy freezes the visual frontend and most of the 12-block
Conformer. It updates the final two Conformer blocks, projection, Transformer
decoder, and CTC head. This is safer than updating all 250 million parameters
from a few hundred recordings.

## 1. Install and authenticate Modal

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-modal.txt
modal setup
```

The Modal application lazily creates three persistent Volumes:

- `silent-lip-reader-data`: uploaded recordings and processed mouth crops
- `silent-lip-reader-runs`: resumable Lightning checkpoints and exported models
- `silent-lip-reader-hf-cache`: pretrained checkpoint and tokenizer cache

## 2. Record a prompted dataset

Use at least three recording sessions and keep sentences disjoint across train,
validation, and test splits. A practical first target is 300 unique prompts,
recorded once while speaking normally and once while mouthing silently.

```text
datasets/elijah/
├── manifest.csv
└── clips/
    ├── session01-0001.mp4
    ├── session01-0002.mp4
    └── ...
```

`manifest.csv` must contain `id,video,text,split`:

```csv
id,video,text,split
session01-0001,clips/session01-0001.mp4,hey how is everyone today,train
session02-0001,clips/session02-0001.mp4,can you tell me the latest with the task,val
session03-0001,clips/session03-0001.mp4,please send the update when it is ready,test
```

Use the displayed prompt as the transcript. Do not create train/test leakage by
putting repetitions or near-duplicates of a test sentence into training.

## 3. Upload and preprocess

```bash
modal volume create silent-lip-reader-data
modal volume put silent-lip-reader-data ./datasets/elijah /elijah
modal run modal_app.py::prepare --dataset-name elijah
```

Preprocessing strips audio, normalizes to 25 fps, aligns the face, writes 96x96
mouth-only videos, normalizes prompt text to the checkpoint's uppercase
SentencePiece vocabulary, and generates the token label files consumed by
Auto-AVSR. Use `--flip` only if the recorded camera file is actually mirrored:

```bash
modal run modal_app.py::prepare --dataset-name elijah --flip
```

## 4. Fine-tune

```bash
modal run --detach modal_app.py::train \
  --dataset-name elijah \
  --run-name elijah-v1 \
  --max-epochs 30
```

The default A10 job saves `last.ckpt` after every epoch and automatically resumes
it when the same run name is launched again. Modal's detached mode lets the job
continue after the terminal closes.

Available strategies:

- `decoder`: decoder and CTC head only
- `encoder-decoder`: projection, last N Conformer blocks, decoder, and CTC
- `full`: every parameter; not recommended for a small personal dataset

Example conservative run:

```bash
modal run --detach modal_app.py::train \
  --dataset-name elijah \
  --run-name elijah-v1 \
  --strategy encoder-decoder \
  --unfreeze-encoder-layers 2 \
  --learning-rate 0.00002
```

## 5. Download and use the personalized checkpoint

```bash
mkdir -p models
modal volume get silent-lip-reader-runs \
  /elijah-v1/personalized_model.pt \
  ./models/elijah-v1.pt
```

Run a clip directly:

```bash
python engine/local_infer.py sample.mp4 \
  --ckpt-path ./models/elijah-v1.pt
```

Or launch the browser application with the personalized model:

```bash
LIPREAD_CKPT=./models/elijah-v1.pt python app.py
```

Always report raw visual-only WER on unseen test sentences before adding an LLM
correction layer. The exported model remains speaker-specific.
