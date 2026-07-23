# Open-Altergo model capability implementation plan

This is the implementation specification for turning upstream checkpoints and
research into selectable Open-Altergo capabilities. It is intentionally tied to
the repository's current modules. The separate
[`PAPER_EXPERIMENTS.md`](PAPER_EXPERIMENTS.md) maps every supplied paper to an
experiment branch.

## 1. Target outcome

Open-Altergo should support several visual-speech backends without teaching
Gradio, HTTP, Swift, or Modal about each model's internal architecture.

The end state is:

```text
video
  -> shared request validation
  -> backend-specific preprocessing
  -> backend-specific visual model and decoder
  -> shared transcription result
  -> Python API / HTTP API / Gradio / Apple clients
```

Training follows the corresponding boundary:

```text
prompted recordings
  -> versioned dataset preparation
  -> backend-compatible examples
  -> initialization policy
  -> local or Modal trainer
  -> exported backend bundle
  -> the same evaluation harness used before training
```

The first useful outcome is not a large refactor. It is a real comparison:

1. current `aaahmet/silent-lip-reader-model` backend;
2. `simonlesaumon/lrs3-lipreader-visual-only`;
3. the same personal dataset fine-tuned from each compatible initialization;
4. raw visual-only results on identical clips;
5. Adam's launch video as a qualitative regression, not a benchmark.

## 2. What exists now

### Current inference path

| Layer | Current source | Current behavior |
| --- | --- | --- |
| Runtime configuration | `apis/python_api/src/core/config.py` | device, detector, one optional checkpoint, enhance flag |
| Interface-neutral service | `apis/python_api/src/core/service.py` | lazily creates one hard-coded `LipReader` |
| Segmentation pipeline | `cloud/engine/src/pipeline.py` | ffmpeg normalization, mouth motion segmentation, per-segment decode |
| Model runtime | `cloud/engine/src/local_infer.py` | hard-coded Auto-AVSR `E2E`, tokenizer, transforms, beam search |
| Asset download | `cloud/engine/src/model_assets.py` | one global manifest and one Hugging Face repository |
| Python consumers | `apps/gradio/app.py`, `apis/http_api/app.py` | call the same service; no backend selection |
| Apple consumer | `apps/apple/API.md` | consumes the HTTP response; backend is invisible |

### Current training path

| Layer | Current source | Current behavior |
| --- | --- | --- |
| Dataset preparation | `training/prepare_dataset.py` | MediaPipe/RetinaFace, 25 fps, 96x96 ROI, current tokenizer labels |
| Personalization module | `training/personalization.py` | decoder, encoder-decoder, or full Auto-AVSR fine-tuning |
| Training entrypoint | `training/train_personal.py` | assumes current `E2E` architecture and tokenizer |
| Modal provisioning | `cloud/modal/app.py` | fixed image, A10 training job, persistent data/run/HF volumes |
| Evaluation | `cloud/engine/src/lightning.py` | test WER only; no prediction artifact, CER, latency, or cohort report |

### Immediate technical gaps

These are capability blockers in the current implementation:

1. `RuntimeConfig` has no backend identifier or model-bundle reference.
2. `_engine_reader_factory()` always imports `pipeline.LipReader`.
3. `LocalVSR` hard-codes one `E2E` architecture and global `TextTransform`.
4. `model_assets.py` assumes one packaged manifest instead of a backend-indexed
   registry.
5. preprocessing is partly embedded in `LocalVSR` and partly in `LipReader`;
   another checkpoint cannot declare a different crop, normalization, or
   tokenizer cleanly.
6. the transcription response has no `backend`, `model_revision`,
   `preprocessing_revision`, or timing diagnostics.
7. HTTP and Gradio have no backend selector.
8. `train_personal.py` assumes every initialization is directly loadable into
   the current model with `load_state_dict`.
9. `run.json` does not contain raw predictions, CER, dataset fingerprint,
   checkpoint fingerprint, best epoch, or baseline comparison.
10. Modal has no inspect, evaluate, compare, export-verify, or experiment-matrix
    function.
11. `training/prepare_dataset.py` references `sys.stderr` in the skip-error path
    without importing `sys`; that path needs a regression test before scaling
    preprocessing.
12. there is no checked-in evaluator for Adam's demo or a general JSONL
    evaluation manifest.

## 3. Backend contract

### 3.1 Backend identifiers

Start with stable identifiers:

```text
auto-avsr-base
lrs3-auto-avsr
vsro-multivsr-ro
personal:<bundle-id>
```

Do not use filenames as backend IDs. A backend identifies architecture and
preprocessing behavior; a model bundle identifies exact weights and tokenizer
assets.

### 3.2 New engine modules

Add:

```text
cloud/engine/src/
├── backends/
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── auto_avsr.py
│   ├── lrs3_auto_avsr.py
│   └── vsro_multivsr.py
├── bundles/
│   ├── __init__.py
│   ├── manifest.py
│   ├── registry.json
│   └── manifests/
│       ├── auto-avsr-base.json
│       ├── lrs3-auto-avsr.json
│       └── vsro-multivsr-ro.json
├── evaluation/
│   ├── __init__.py
│   ├── manifests.py
│   ├── metrics.py
│   ├── runner.py
│   └── reporting.py
├── inspection/
│   ├── __init__.py
│   ├── checkpoint.py
│   └── compatibility.py
└── schemas.py
```

These folders remain directly under `cloud/engine/src`; do not add another
redundant `open_altergo_engine/` directory.

### 3.3 Python protocol

`backends/base.py` should define the minimum contract:

```python
class VisualSpeechBackend(Protocol):
    backend_id: str
    bundle: ModelBundle
    preprocessing: PreprocessingSpec

    def transcribe(
        self,
        path: str,
        *,
        nbest: int,
        hflip: bool,
        max_seconds: int,
    ) -> TranscriptionResult: ...

    def transcribe_auto(
        self,
        path: str,
        *,
        nbest: int,
        max_seconds: int,
    ) -> TranscriptionResult: ...

    def encode_video(self, path: str) -> EncodedSequence: ...
```

`encode_video()` is required because VSRo transfer and LRRo-style probes need
encoder representations without running the sentence decoder.

Optional capabilities must be declared rather than guessed:

```python
BackendCapabilities(
    sentence_transcription=True,
    nbest=True,
    encoder_features=True,
    trainable=True,
    supports_personalization=True,
    languages=("en",),
)
```

### 3.4 Preprocessing specification

Each backend bundle declares:

```json
{
  "fps": 25,
  "face_detector": "mediapipe",
  "alignment": "four-keypoint-affine",
  "roi_height": 96,
  "roi_width": 96,
  "tensor_crop": 88,
  "color": "grayscale",
  "mean": 0.421,
  "std": 0.165,
  "max_segment_seconds": 16,
  "horizontal_flip_policy": "caller-or-auto",
  "audio_policy": "strip"
}
```

The LRS3 candidate must not inherit these values automatically. Its pinned code
and model card determine its spec. A preprocessing mismatch is a failed
integration even if tensor shapes happen to load.

### 3.5 Model bundle manifest v2

Replace the single global assumption with one manifest per bundle:

```json
{
  "schema_version": 2,
  "bundle_id": "lrs3-auto-avsr@<revision>",
  "backend_id": "lrs3-auto-avsr",
  "repository_id": "simonlesaumon/lrs3-lipreader-visual-only",
  "revision": "<40-character-hugging-face-commit>",
  "architecture_revision": "<40-character-code-commit>",
  "files": {
    "model_avg_10.pth": {
      "role": "model-state",
      "size": 0,
      "sha256": "<sha256>",
      "format": "pytorch"
    }
  },
  "tokenizer": {
    "kind": "sentencepiece",
    "source": "embedded-or-file",
    "vocabulary_size": 0,
    "language": "en"
  },
  "preprocessing": {},
  "training": {
    "dataset": "Ainncy/LRS3 trainval",
    "epochs": 20
  }
}
```

`model_assets.py` remains as a compatibility wrapper for the current bundle.
New code resolves a `bundle_id`, downloads all declared files at the declared
revision, checks size and SHA-256, and returns a read-only `ResolvedBundle`.

### 3.6 Shared result schema

Add typed dataclasses or `TypedDict`s in `cloud/engine/src/schemas.py`:

```json
{
  "schema_version": 1,
  "request_id": "optional",
  "backend": "lrs3-auto-avsr",
  "bundle_id": "lrs3-auto-avsr@...",
  "preprocessing_revision": "preprocess-v1",
  "segments": [
    {
      "seg_frames": [0, 75],
      "seg_time": [0.0, 3.0],
      "text": "hello world",
      "nbest": [
        {"text": "hello world", "score": -1.23}
      ]
    }
  ],
  "transcript": "hello world",
  "n_segments": 1,
  "diagnostics": {
    "input_seconds": 3.0,
    "decoded_frames": 75,
    "face_detection_ms": 0.0,
    "preprocessing_ms": 0.0,
    "inference_ms": 0.0,
    "total_ms": 0.0,
    "real_time_factor": 0.0,
    "hflip": false,
    "no_face": false
  }
}
```

Keep the current top-level keys so existing clients remain compatible. New
fields are additive.

## 4. Phase 0 — make comparisons trustworthy

This phase changes no model output.

### P0.1 Extract and preserve the current backend

Move the current `LocalVSR` behavior behind `backends/auto_avsr.py`.

Acceptance:

- the existing manifest revision and hashes remain identical;
- old `LIPREAD_CKPT` behavior still works;
- the 21 current tests pass unchanged before new assertions are added;
- fixed local fixtures produce byte-for-byte identical transcript JSON after
  removing newly added diagnostic timing values.

### P0.2 Add backend selection

Change `RuntimeConfig`:

```python
backend: str = "auto-avsr-base"
bundle: str | None = None
checkpoint_path: str | None = None
```

Environment mapping:

```text
OPEN_ALTERGO_BACKEND
OPEN_ALTERGO_BUNDLE
LIPREAD_CKPT
```

`LIPREAD_CKPT` remains a backward-compatible override for a current-architecture
personal checkpoint. It must not silently force unrelated checkpoint formats
into the current `E2E` class.

Change `_engine_reader_factory()` to call:

```python
create_backend(config.backend, config)
```

Tests:

- default backend remains `auto-avsr-base`;
- an unknown backend fails before downloading a model;
- backend construction remains lazy;
- two services configured with different backends do not share model state;
- a personal bundle is resolved to the correct architecture.

### P0.3 Add evaluation manifests

Add:

```text
benchmarks/
├── README.md
├── manifests/
│   ├── schema.json
│   └── example.jsonl
└── qualitative/
    └── adam-launch/
        └── README.md
```

Videos stay ignored. A JSONL row:

```json
{
  "id": "session03-0042",
  "video": "clips/session03-0042.mp4",
  "reference": "please send the update when it is ready",
  "speaker_id": "speaker-a",
  "session_id": "session03",
  "language": "en",
  "domain": "prompted",
  "lighting": "indoor-front",
  "camera": "iphone-front",
  "silent": true,
  "qualitative_only": false
}
```

Adam's video row uses `qualitative_only: true` unless a verified verbatim
reference transcript is manually created. It must never affect WER averages.

### P0.4 Add evaluator and reports

Proposed commands:

```bash
python -m open_altergo_engine.evaluation.runner \
  --manifest benchmarks/manifests/personal-test.jsonl \
  --backend auto-avsr-base \
  --output runs/eval/base

python -m open_altergo_engine.evaluation.runner \
  --manifest benchmarks/manifests/personal-test.jsonl \
  --backend lrs3-auto-avsr \
  --output runs/eval/lrs3

python -m open_altergo_engine.evaluation.reporting compare \
  runs/eval/base/results.jsonl \
  runs/eval/lrs3/results.jsonl \
  --output runs/eval/comparison
```

Every evaluation directory contains:

```text
run.json
results.jsonl
summary.json
failures.jsonl
report.md
```

Required summary metrics:

- WER and CER overall;
- sentence exact-match rate;
- no-face and preprocessing-failure rates;
- median and p95 real-time factor;
- median and p95 total latency;
- peak CPU/GPU memory when measurable;
- metrics by speaker, session, camera, lighting, silence mode, and domain;
- bootstrap confidence intervals for WER difference;
- raw and text-normalized predictions;
- count of clips excluded and exact exclusion reason.

The normalizer must be versioned and applied equally to every backend.

### P0.5 Fix preparation and evaluation gaps

Before large jobs:

- import `sys` in `training/prepare_dataset.py`;
- test `--skip-errors`;
- make ffmpeg failure include stderr and return code;
- reject zero-frame normalized videos;
- fingerprint source manifest and generated label files;
- make test decoding emit every prediction/reference pair;
- compute CER as well as WER;
- guard division by zero for empty test references;
- record seed, dependency versions, device, git revision, bundle ID, and
  preprocessing revision in every run.

## 5. Phase 1 — ingest the LRS3 visual-only checkpoint

### P1.1 Resolve upstream artifacts

Required facts:

- full 40-character Hugging Face revision;
- complete file tree and file sizes;
- SHA-256 for every required asset;
- full Auto-AVSR code revision corresponding to short commit `182b628`;
- checkpoint container structure;
- tokenizer source and vocabulary;
- exact model hyperparameters;
- input crop, frame rate, normalization, maximum length, and decoder settings.

The current `git ls-remote` attempt hangs in this environment. On a connected
machine:

```bash
git ls-remote \
  https://huggingface.co/simonlesaumon/lrs3-lipreader-visual-only \
  refs/heads/main

pretraining/lrs3-lipreader-visual-only/download.sh <full-revision>
```

Commit the resolved metadata and hashes, not the downloaded checkpoint.

### P1.2 Add checkpoint inspection

Add:

```bash
python -m open_altergo_engine.inspection.checkpoint \
  pretraining/.cache/lrs3-lipreader-visual-only/<revision>/model_avg_10.pth \
  --output runs/inspection/lrs3.json
```

Inspection output must include:

- top-level object type and keys;
- whether weights are a raw state dict, Lightning checkpoint, or nested model;
- every tensor name, shape, dtype, parameter count, and byte count;
- non-tensor keys without executing imported application code;
- duplicate/shared storage where detectable;
- candidate prefix transformations such as `model.` removal;
- inferred frontend, encoder, decoder, and CTC groups;
- comparison with a freshly instantiated current `E2E` state dict.

Compatibility report categories:

```text
exact
prefix-only
same-architecture-different-vocabulary
partial-encoder-compatible
incompatible
```

Do not write an adapter before this report establishes which case applies.

### P1.3 Implement the correct compatibility branch

#### Case A — exact or prefix-only

- instantiate current `E2E`;
- normalize checkpoint prefixes;
- require 100% tensor-name and tensor-shape coverage;
- load with `strict=True`;
- reuse tokenizer only if its hash and vocabulary are identical;
- add `lrs3_auto_avsr.py` as a thin manifest/preprocessing specialization.

#### Case B — same encoder/decoder structure, different vocabulary

- load frontend, projection, and encoder strictly;
- instantiate the decoder/CTC dimensions from the LRS3 tokenizer;
- load decoder and CTC only when their output shapes match that tokenizer;
- prohibit use of the current `unigram5000` tokenizer;
- export the tokenizer as part of the resolved model bundle.

#### Case C — partially compatible encoder

- implement a dedicated architecture adapter matching pinned upstream code;
- expose the same `VisualSpeechBackend` contract;
- map shared encoder representations only through explicit tensor-by-tensor
  tests;
- do not patch the current `E2E` class with model-specific conditionals.

#### Case D — incompatible

- keep the source as a separate backend implementation;
- decide whether reproducing the upstream environment is worth the maintenance
  cost based on actual Adam-video and held-out results;
- do not force-load tensors or ignore broad missing/unexpected-key sets.

### P1.4 Preprocessing parity tests

Create a fixed tiny video fixture and compare upstream versus Open-Altergo:

- frame count after normalization;
- aligned ROI coordinates;
- ROI tensor shape;
- mean/std after normalization;
- maximum absolute tensor difference;
- horizontal orientation;
- segmentation boundaries;
- tokenizer IDs for at least 100 representative English sentences;
- decoded output under greedy and configured beam decoding.

Target:

- identical preprocessing where upstream code is deterministic;
- otherwise document the exact difference and run an ablation proving it does
  not account for the model comparison.

### P1.5 Expose selection through every interface

#### Python API

```python
service = SilentSpeechService(
    RuntimeConfig(backend="lrs3-auto-avsr")
)
```

#### HTTP API

Initially select the server backend through deployment configuration, not an
untrusted per-request form field:

```text
OPEN_ALTERGO_BACKEND=lrs3-auto-avsr
```

Add backend and bundle ID to `/health`:

```json
{
  "status": "ok",
  "model_loaded": false,
  "backend": "lrs3-auto-avsr",
  "bundle_id": "lrs3-auto-avsr@..."
}
```

An administrative multi-backend deployment may later accept a validated
`backend` request field. Do not let clients request arbitrary repository IDs or
local paths.

#### Gradio

Development mode may expose a dropdown populated from the registry:

```text
Auto-AVSR base
LRS3 visual-only
Personal bundle
```

The result view should show backend, total time, and real-time factor while
keeping the transcript prominent.

#### Apple

The Apple client does not need model code. It decodes additive backend metadata
and can show it in a diagnostics sheet. Its capture/upload path remains the
same.

### P1.6 Adam launch-demo regression

Expected local location:

```text
benchmarks/qualitative/adam-launch/hRU_uIH4p3fTEhnH.mp4
```

The video is not currently present in this checkout. The regression command
must fail with a clear missing-asset message rather than silently skipping it.

Run matrix:

| Variant | Backend | Orientation | Segmentation |
| --- | --- | --- | --- |
| A | current base | normal | motion |
| B | current base | flipped | motion |
| C | LRS3 | normal | motion |
| D | LRS3 | flipped | motion |
| E | current base | best orientation | whole clip/chunk limit |
| F | LRS3 | best orientation | whole clip/chunk limit |

Save:

- normalized muted video metadata;
- face/ROI failure counts;
- segment boundaries;
- top five hypotheses and scores per segment;
- complete transcript;
- load, preprocessing, and decode times;
- backend/bundle hashes;
- optional manually verified reference transcript;
- side-by-side Markdown report.

This answers whether we can reproduce the visible launch behavior. It does not
establish general WER.

### P1.7 Phase acceptance

Phase 1 is complete when:

- the candidate bundle resolves by immutable ID;
- all files verify;
- compatibility classification is stored;
- preprocessing parity is tested;
- Python API, HTTP API, and Gradio all work with the backend;
- current-backend regression tests remain green;
- Adam's video produces a saved side-by-side report;
- a held-out manifest produces comparable WER/CER and latency reports.

## 6. Phase 2 — Modal personalization from selectable initializations

### P2.1 Separate training architecture from initialization

Add training configuration:

```text
--backend
--initial-bundle
--initial-checkpoint
--initialization-mode full|encoder|frontend
--tokenizer-policy require-match|replace-heads
```

`--initial-checkpoint` remains for local debugging. Modal jobs should normally
use immutable bundle IDs.

The trainer must validate before allocating a GPU:

- backend supports training;
- checkpoint architecture compatibility;
- tokenizer compatibility;
- decoder/CTC output dimension;
- preprocessing revision matches prepared data;
- dataset label vocabulary contains no invalid IDs.

### P2.2 Dataset contract v2

Extend input manifest:

```csv
id,video,text,split,speaker_id,session_id,camera,silent,prompt_id,prompt_revision
```

Required split policy:

- session-disjoint validation and test;
- prompt text disjoint across splits unless explicitly testing repetition;
- no near-duplicate video hashes across splits;
- both normally voiced and silently mouthed clips tagged;
- minimum clip/frame validation before upload;
- exact prompt and correction history retained in local/Modal metadata.

Preparation output adds:

```text
dataset.json
metadata.jsonl
failures.jsonl
labels/
preprocessing.json
SHA256SUMS
```

`dataset.json` records:

- dataset ID and content fingerprint;
- manifest fingerprint;
- split counts/durations;
- speaker/session counts;
- tokenizer/bundle ID;
- preprocessing revision;
- failure summary;
- generated artifact hashes.

### P2.3 Fine-tuning matrix

Run the same seed set and splits:

| Run | Initialization | Trainable components |
| --- | --- | --- |
| B0 | current base | none; evaluation baseline |
| B1 | LRS3 base | none; evaluation baseline |
| F1 | current base | decoder + CTC |
| F2 | current base | projection + last 2 encoder blocks + decoder + CTC |
| F3 | current base | full model |
| F4 | LRS3 base | decoder + CTC |
| F5 | LRS3 base | projection + last 2 encoder blocks + decoder + CTC |
| F6 | LRS3 base | full model |

If the LRS3 tokenizer differs:

- add `encoder-transfer` runs with newly initialized English output heads;
- do not compare early epochs against full-model warm starts without labeling
  the difference;
- record frozen/trainable parameter counts for every run.

Use at least three seeds for any claim that one method is better. A single run
may validate plumbing but not establish a quality result.

### P2.4 Modal functions

Extend `cloud/modal/app.py`:

```text
inspect_bundle(bundle_id)
prepare(dataset_name, backend, ...)
evaluate(dataset_name, backend, bundle_id, run_name)
train(dataset_name, run_name, backend, initial_bundle, ...)
compare(run_names, output_name)
export_verify(run_name)
```

GPU selection:

- inspection/preparation: CPU unless tensor loading requires GPU;
- smoke training: L4 or A10;
- standard personalization: A10;
- 250M full fine-tuning or larger batches: A100-80GB when A10 memory is
  insufficient;
- record actual GPU and hourly/runtime cost metadata.

The training job should not use automatic retries for deterministic code or
data errors. Retry only provider interruption/preemption, and preserve the
original failure in run metadata.

### P2.5 Training artifacts

Each run directory:

```text
runs/<run-name>/
├── arguments.json
├── environment.json
├── dataset.json
├── initialization.json
├── last.ckpt
├── best.ckpt
├── personalized_model.pt
├── bundle.json
├── metrics.csv
├── predictions-val.jsonl
├── predictions-test.jsonl
├── failures.jsonl
├── run.json
└── report.md
```

`run.json` must contain:

- status: running/succeeded/failed/interrupted;
- git commit and dirty-state marker;
- backend and initial bundle;
- dataset and preprocessing fingerprints;
- arguments and seed;
- dependency versions and GPU;
- epoch/step counts;
- best epoch/checkpoint;
- trainable/total parameters;
- validation loss, WER, CER;
- held-out WER, CER, exact-match rate;
- no-face/preprocessing failure counts from pre-training evaluation;
- artifact filenames, sizes, and SHA-256 values;
- baseline deltas;
- wall-clock and estimated compute cost.

### P2.6 Export verification

`export_verify` must:

1. load the exported bundle in a fresh single-use container;
2. run fixed smoke clips;
3. compare predictions with the best Lightning checkpoint;
4. assert expected tensor coverage;
5. assert tokenizer and preprocessing IDs;
6. produce a verification JSON;
7. mark the bundle activatable only on success.

### P2.7 Modal commands

Target commands:

```bash
doppler run -p seed -c prd -- \
  modal run cloud/modal/app.py::inspect_bundle \
  --bundle-id lrs3-auto-avsr@<revision>

doppler run -p seed -c prd -- \
  modal run cloud/modal/app.py::prepare \
  --dataset-name elijah \
  --backend lrs3-auto-avsr

doppler run -p seed -c prd -- \
  modal run --detach cloud/modal/app.py::train \
  --dataset-name elijah \
  --run-name elijah-lrs3-encdec-s42 \
  --backend lrs3-auto-avsr \
  --initial-bundle lrs3-auto-avsr@<revision> \
  --strategy encoder-decoder \
  --unfreeze-encoder-layers 2 \
  --max-epochs 30

doppler run -p seed -c prd -- \
  modal run cloud/modal/app.py::export_verify \
  --run-name elijah-lrs3-encdec-s42
```

### P2.8 Phase acceptance

- at least one real Modal run completes;
- exported weights reload in a fresh container;
- raw validation/test predictions exist;
- WER/CER and baseline deltas are reported;
- every interface can select the exported personal bundle;
- resuming produces the same run lineage instead of overwriting provenance;
- failure/retry behavior is tested.

## 7. Phase 3 — VSRo-200 capabilities

VSRo has three distinct assets. Do not merge them conceptually.

### P3.1 Romanian sentence backend

Use `vsro200/models-vsro200` plus the pinned GitHub architecture to implement
`vsro-multivsr-ro`.

Required work:

- pin the actual model repository revision and target checkpoint;
- pin MultiVSR instead of shallow-cloning its moving branch;
- pin/checksum the VTP feature extractor;
- package the Romanian tokenizer;
- reproduce one upstream sample prediction;
- add Romanian text normalization;
- expose encoder features through `encode_video()`;
- report `.pt` key compatibility and load coverage.

This backend's sentence decoder is Romanian. Its direct success criterion is
reproducing Romanian inference, not Adam's English transcript.

### P3.2 English transfer experiment

Compare:

| Variant | VSRo components transferred | English components initialized |
| --- | --- | --- |
| V0 | none | current base |
| V1 | VTP frontend only | current projection/encoder/decoder |
| V2 | frontend + VSR encoder | new/current English decoder and CTC |
| V3 | frozen VSRo encoder | lightweight English probe |
| V4 | VSRo encoder partially unfrozen | English decoder and CTC |
| V5 | VSRo encoder fully unfrozen | English decoder and CTC |

Measurements:

- initial English WER/CER before fine-tuning;
- steps and wall-clock time to reach fixed WER thresholds;
- best held-out WER/CER;
- catastrophic forgetting on a Romanian smoke subset where applicable;
- trainable parameter count and memory;
- representation-probe accuracy.

The useful outcome may be faster personalization rather than better zero-shot
English transcription.

### P3.3 Pseudo-label scaling

Reproduce the methodology on authorized English data:

```text
10h, 25h, 50h, 75h, 100h human labels
10h, 25h, 50h, 75h, 100h, 125h, 150h, 175h, 200h pseudo labels
```

If those scales are unavailable, preserve ratios and publish actual hours.

Each pseudo-labeled row records:

- teacher bundle and revision;
- raw teacher transcript;
- normalized transcript;
- teacher confidence signals;
- filtering reason;
- human correction if any;
- source clip hash.

Compare equal-hour human/pseudo subsets before attributing a result to label
quality. Then compare additional pseudo-labeled hours to measure scalability.

### P3.4 Seen/unseen and OOD framework

Add split dimensions:

```text
speaker_seen
speaker_unseen
camera_seen
camera_unseen
domain
lighting
resolution
motion_blur
pose
vocabulary_domain
```

Initial OOD suites:

- webcam versus phone;
- frontal versus moderate off-axis pose;
- bright versus low light;
- stable versus handheld;
- clean versus compressed/blurred;
- prompted everyday language versus technical vocabulary;
- normal articulation versus silent mouthing.

Record OOV token and type rates so vocabulary shift is not confused with visual
degradation.

## 8. Phase 4 — generic representation probe

The LRRo MLP is a word classifier, not a sentence decoder. Its transferable
capability is a cheap measurement of encoder quality.

### P4.1 Modules

Add:

```text
cloud/engine/src/probes/
├── __init__.py
├── pooling.py
├── classifier.py
├── dataset.py
├── train.py
└── evaluate.py
```

Pooling options:

- masked mean;
- masked max;
- attention pooling matching the pinned VSRo methodology;
- optional learned class token only as a separate ablation.

Classifier:

```text
encoder sequence -> pooling -> LayerNorm -> MLP -> word logits
```

### P4.2 Standard experiment

Freeze each encoder:

```text
auto-avsr-base
lrs3-auto-avsr
vsro-multivsr-ro
personal bundles
```

Train identical probe heads with identical splits and seeds. Report:

- top-1 and top-5 accuracy;
- macro F1;
- per-class precision/recall;
- confusion matrix;
- calibration error;
- parameter count and training time;
- linear/attention probe comparison.

The probe dataset must use disjoint speakers and recording sessions. A model
that memorizes the speaker/camera is not demonstrating word separability.

### P4.3 Diagnostic use

Use the probe to answer:

- did personalization improve visual features or only the decoder?
- does VSRo transfer provide separable English mouth-motion features?
- does a new Swin/multi-scale encoder improve representations before language
  modeling hides the difference?
- which word/viseme pairs remain visually confused?

## 9. Research capability branches

All supplied papers are mapped in
[`PAPER_EXPERIMENTS.md`](PAPER_EXPERIMENTS.md). They feed these branches:

```text
Branch A: raw visual recognition and historical baselines
Branch B: phoneme/viseme units and language-model decoding
Branch C: cross-modal distillation and pseudo-label supervision
Branch D: efficient/multi-scale visual encoders
Branch E: multilingual and context-aware recognition
Branch F: active-speaker, integrity, and synthetic-data tooling
Branch G: lip-to-speech and synchronized output
Branch H: audio-visual separation
```

Do not combine branches in the first experiment. Each capability needs an
isolated baseline and ablation before stacking.

## 10. Interface and API changes

### Python API

Add:

```python
RuntimeConfig.backend
RuntimeConfig.bundle
SilentSpeechService.backend_info
SilentSpeechService.list_backends()
SilentSpeechService.encode_video()
```

`encode_video()` may be marked experimental and omitted from HTTP until an
actual consumer exists.

### HTTP API

Additive `/health` fields first. Then add:

```text
GET /v1/capabilities
```

Response:

```json
{
  "backends": [
    {
      "id": "auto-avsr-base",
      "languages": ["en"],
      "sentence_transcription": true,
      "personalization": true,
      "active": true
    }
  ]
}
```

Keep model activation server-side. Later personalization endpoints may activate
a user-scoped bundle, but request bodies must reference registry IDs, never
arbitrary download URLs.

### Gradio

Add development controls:

- backend dropdown;
- orientation: normal/flipped/auto;
- segmentation: motion/whole-clip;
- N-best count;
- diagnostics expander;
- side-by-side compare action.

The public demo can hide experimental controls and use the deployment default.

### Apple

Update Swift fixtures for additive backend fields and `/v1/capabilities`.
Backend selection should be a developer/debug setting until multiple deployed
backends are stable. No model-specific preprocessing belongs in Swift unless an
on-device backend is intentionally created later.

## 11. Test plan

### Unit tests

Add:

```text
tests/test_backend_registry.py
tests/test_bundle_manifests.py
tests/test_checkpoint_inspection.py
tests/test_preprocessing_specs.py
tests/test_evaluation_metrics.py
tests/test_evaluation_manifests.py
tests/test_training_initialization.py
tests/test_training_artifacts.py
tests/test_representation_probe.py
```

Required assertions:

- registry rejects duplicate/unknown backend IDs;
- manifests require immutable revisions and hashes before resolution;
- checksum retry behavior remains bounded;
- incompatible tensor shapes fail before training;
- tokenizers cannot be mixed silently;
- normalization is deterministic;
- qualitative-only rows never enter aggregate WER;
- empty references and failed clips are accounted for;
- run artifacts contain required fingerprints;
- personal bundles reload through their declared backend.

### Integration tests

- current backend transcription with mocked assets;
- LRS3 adapter with a tiny synthetic state dict matching expected keys;
- HTTP health reports backend without loading it;
- Gradio selection constructs the requested backend lazily;
- preparation produces dataset fingerprints;
- one CPU single-batch training smoke test;
- export and reload predictions match;
- Modal command construction passes bundle/backend arguments.

### GPU tests

- one forward/decode for each real backend;
- one optimizer step for each supported fine-tuning strategy;
- mixed precision stability;
- peak-memory capture;
- exported checkpoint parity.

### End-to-end tests

- video -> Python API -> transcript;
- video upload -> HTTP -> transcript;
- Gradio handler -> selected backend;
- prepared personal dataset -> Modal train -> export -> activate -> transcript;
- Adam video -> two-backend comparison report.

## 12. Execution order

### Milestone M0 — trustworthy baseline

Files:

- `cloud/engine/src/schemas.py`
- `cloud/engine/src/backends/base.py`
- `cloud/engine/src/backends/registry.py`
- `cloud/engine/src/backends/auto_avsr.py`
- `cloud/engine/src/evaluation/*`
- `apis/python_api/src/core/config.py`
- `apis/python_api/src/core/service.py`

Exit:

- current behavior preserved;
- backend ID visible;
- evaluator produces full baseline artifacts.

### Milestone M1 — LRS3 candidate

Files:

- resolved LRS3 manifest;
- `cloud/engine/src/inspection/*`;
- `cloud/engine/src/backends/lrs3_auto_avsr.py`;
- preprocessing parity fixtures;
- API/Gradio backend-selection tests.

Exit:

- real candidate loads and decodes;
- Adam comparison exists;
- held-out comparison exists.

### Milestone M2 — selectable personalization

Files:

- generalized training initialization;
- dataset contract v2;
- expanded Modal functions;
- export verification;
- activation through Python/HTTP/Gradio.

Exit:

- real fine-tune from candidate initialization;
- held-out metrics and raw predictions;
- exported bundle reloads everywhere.

### Milestone M3 — VSRo transfer and probes

Files:

- VSRo backend and bundle;
- representation probe package;
- transfer experiment configs;
- OOD/cohort report support.

Exit:

- Romanian upstream sample reproduced;
- English transfer report completed;
- three encoders compared with the same probe.

### Milestone M4 — paper-derived improvements

Run paper branches in the priority order defined in
`PAPER_EXPERIMENTS.md`. Promote only isolated wins.

## 13. Initial decision rules

These are experiment decisions, not product promises.

Promote a candidate backend from experimental to supported when:

- it completes the full held-out manifest with no unexplained failures;
- preprocessing and tokenizer are versioned;
- bundle resolution is deterministic;
- WER/CER is better, or a documented latency/memory advantage justifies a
  bounded quality tradeoff;
- p95 latency and peak memory fit the intended deployment;
- current interfaces require no model-specific code;
- export/reload parity passes.

Promote a personalization strategy when:

- improvement repeats across at least three seeds;
- it improves speaker/session-disjoint test WER, not only training loss;
- no-face and preprocessing failure rates do not hide hard examples;
- raw predictions show meaningful visual adaptation rather than prompt
  memorization;
- the exported bundle passes fresh-container verification.

Stop an experiment when:

- the architecture cannot expose the required backend contract without
  maintaining a fork of unrelated infrastructure;
- the result depends on changing normalization, test data, or language-model
  correction in only one arm;
- gains disappear on speaker/session-disjoint data;
- compute cost or latency is dominated without a measurable capability gain.

## 14. Definition of capability complete

A capability is complete only when it has:

1. a stable backend or experiment ID;
2. immutable input/model/data fingerprints;
3. a command that runs without editing source;
4. typed inputs and outputs;
5. unit and integration tests;
6. a real run artifact;
7. raw predictions or measurements;
8. comparison against the current baseline;
9. a documented failure mode;
10. a clear interface exposure or a deliberate decision to remain internal.

Anything less is a research note, not an Open-Altergo capability.
