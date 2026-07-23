# Model capability execution queue

This queue implements [`CAPABILITY_PLAN.md`](CAPABILITY_PLAN.md). Paper-specific
experiment definitions are in [`PAPER_EXPERIMENTS.md`](PAPER_EXPERIMENTS.md).
The tasks are separate from the Apple client queue.

## Foundation

- [ ] **PT-000 — Repair preparation and evaluation prerequisites**
  - Dependencies: none.
  - Change:
    - import `sys` in `training/prepare_dataset.py`;
    - test `--skip-errors`;
    - capture ffmpeg return code/stderr;
    - reject zero-frame normalized output;
    - guard test WER against empty references;
    - emit raw prediction/reference pairs and CER.
  - Tests:
    - failed sample is recorded and the next sample proceeds;
    - invalid video produces a typed failure;
    - empty test set cannot report a misleading zero metric.
  - Acceptance: preparation and evaluation failure paths are deterministic and
    tested.
  - Evidence: `TBD`

- [ ] **PT-001 — Resolve the LRS3 model bundle**
  - Dependencies: none.
  - Source: `simonlesaumon/lrs3-lipreader-visual-only`.
  - Resolve:
    - full Hugging Face revision;
    - full architecture revision for short commit `182b628`;
    - complete file inventory, sizes, and SHA-256 values;
    - tokenizer/vocabulary;
    - crop, fps, normalization, length, and decode configuration.
  - Update:
    - `pretraining/lrs3-lipreader-visual-only/source.json`;
    - backend bundle manifest.
  - Acceptance: the downloader retrieves an immutable bundle and every file
    verifies without committing weights.
  - Evidence: `PARTIAL: model card supplied; Hub lookup currently hangs`

- [ ] **PT-002 — Freeze the current Auto-AVSR baseline**
  - Dependencies: PT-000.
  - Record:
    - current bundle revision and hashes;
    - architecture/tensor inventory;
    - tokenizer hash;
    - preprocessing spec;
    - decoder defaults;
    - transcript fixtures with timing fields removed.
  - Acceptance: moving the implementation behind a backend interface causes no
    output regression.
  - Evidence: `current model bundle already pinned; evaluator not implemented`

- [ ] **PT-003 — Add backend and bundle registries**
  - Dependencies: PT-002.
  - Add:
    - `cloud/engine/src/backends/base.py`;
    - `cloud/engine/src/backends/registry.py`;
    - `cloud/engine/src/backends/auto_avsr.py`;
    - `cloud/engine/src/bundles/manifest.py`;
    - `cloud/engine/src/bundles/registry.json`;
    - `cloud/engine/src/schemas.py`.
  - Change:
    - `RuntimeConfig.backend` and `.bundle`;
    - `SilentSpeechService` construction through the registry;
    - additive backend metadata in results.
  - Tests:
    - default remains lazy;
    - unknown backend fails before download;
    - duplicate IDs fail registry validation;
    - different backend services do not share state.
  - Acceptance: the current backend runs through the registry and all existing
    interfaces remain functional.
  - Evidence: `TBD`

- [ ] **PT-004 — Build the evaluation harness**
  - Dependencies: PT-000, PT-003.
  - Add:
    - JSONL benchmark manifest parser;
    - versioned text normalizer;
    - WER/CER/exact-match and cohort metrics;
    - latency/RTF/memory collection;
    - results, failures, summary, and Markdown reporting;
    - comparison command with bootstrap WER-difference intervals.
  - Required output:
    - `run.json`;
    - `results.jsonl`;
    - `failures.jsonl`;
    - `summary.json`;
    - `report.md`.
  - Tests:
    - qualitative-only examples never enter aggregate WER;
    - exclusions remain counted;
    - empty references do not divide by zero;
    - normalization is identical across backends.
  - Acceptance: one command evaluates the current backend on a manifest and a
    second command compares two result directories.
  - Evidence: `TBD`

## LRS3 and Adam-demo capability

- [ ] **PT-005 — Inspect LRS3 checkpoint compatibility**
  - Dependencies: PT-001, PT-003.
  - Add:
    - checkpoint inventory CLI;
    - tensor-name/shape comparison;
    - prefix-normalization suggestions;
    - classification as exact, prefix-only, vocabulary-different,
      encoder-compatible, or incompatible.
  - Acceptance: a checked-in JSON report determines which adapter branch to
    implement; no broad `strict=False` loading is used as a substitute.
  - Evidence: `TBD`

- [ ] **PT-006 — Implement the LRS3 backend**
  - Dependencies: PT-005.
  - Add:
    - `cloud/engine/src/backends/lrs3_auto_avsr.py`;
    - LRS3 bundle manifest;
    - tokenizer/preprocessing adapter where required.
  - Change:
    - Python API backend selection;
    - deployment-configured HTTP backend;
    - development Gradio backend selector;
    - additive backend information in `/health` and transcription results.
  - Tests:
    - strict tensor coverage;
    - tokenizer mismatch rejection;
    - preprocessing tensor parity;
    - Python/HTTP/Gradio lazy selection;
    - current backend remains the default.
  - Acceptance: `lrs3-auto-avsr` decodes a real video through every current
    interface.
  - Evidence: `TBD`

- [ ] **PT-007 — Run the Adam launch-video comparison**
  - Dependencies: PT-004, PT-006.
  - Required local asset:
    - `benchmarks/qualitative/adam-launch/hRU_uIH4p3fTEhnH.mp4`.
  - Matrix:
    - current and LRS3 backends;
    - normal and flipped orientation;
    - motion segmentation and whole-clip/chunked decode.
  - Save:
    - segment boundaries;
    - top-five hypotheses;
    - transcripts;
    - backend/bundle hashes;
    - preprocessing and decode times;
    - face/preprocessing failures;
    - side-by-side report.
  - Acceptance: the qualitative report is reproducible from one command and is
    excluded from aggregate WER unless a verified reference is added.
  - Evidence: `BLOCKED: video is not present in this checkout`

## Personalization capability

- [ ] **PT-008 — Implement dataset contract v2**
  - Dependencies: PT-000, PT-003.
  - Add manifest fields:
    - speaker/session/camera;
    - silent/voiced;
    - prompt ID and revision.
  - Enforce:
    - session-disjoint val/test;
    - prompt-disjoint splits;
    - duplicate video detection;
    - tokenizer ID validation;
    - preprocessing/bundle fingerprints.
  - Output:
    - `dataset.json`, `metadata.jsonl`, `failures.jsonl`,
      `preprocessing.json`, labels, and `SHA256SUMS`.
  - Acceptance: the same prepared dataset can be proved compatible or
    incompatible with a requested backend before GPU allocation.
  - Evidence: `TBD`

- [ ] **PT-009 — Generalize training initialization**
  - Dependencies: PT-003, PT-006, PT-008.
  - Add:
    - backend and initial-bundle arguments;
    - full/encoder/frontend initialization modes;
    - require-match/replace-head tokenizer policy;
    - architecture compatibility preflight.
  - Preserve fine-tuning strategies:
    - decoder;
    - encoder-decoder;
    - full.
  - Tests:
    - exact checkpoint load;
    - prefix-only conversion;
    - output-head mismatch rejection;
    - encoder transfer with new heads;
    - frozen module eval state.
  - Acceptance: current and LRS3 initializations use the same entrypoint without
    architecture-specific code in `train_personal.py`.
  - Evidence: `TBD`

- [ ] **PT-010 — Expand Modal into an experiment runner**
  - Dependencies: PT-004, PT-009.
  - Add Modal functions:
    - `inspect_bundle`;
    - backend-aware `prepare`;
    - `evaluate`;
    - backend-aware `train`;
    - `compare`;
    - `export_verify`.
  - Persist:
    - dataset/initialization fingerprints;
    - environment and GPU;
    - raw val/test predictions;
    - WER/CER and baseline deltas;
    - checkpoint/export hashes;
    - wall-clock and compute metadata.
  - Acceptance: a fresh single-use container reloads an export and matches the
    best training checkpoint on fixed smoke clips.
  - Evidence: `TBD`

- [ ] **PT-011 — Run the current-versus-LRS3 personalization matrix**
  - Dependencies: PT-010.
  - Runs:
    - both untrained baselines;
    - decoder-only from each;
    - last-two-encoder-blocks plus decoder from each;
    - full fine-tuning from each.
  - Repeat quality claims across at least three seeds.
  - Acceptance: report includes held-out WER/CER, raw predictions, convergence
    speed, parameters, memory, time, and export verification.
  - Evidence: `TBD`

## VSRo and representation capability

- [ ] **PT-012 — Implement the VSRo Romanian backend**
  - Dependencies: PT-003, PT-004.
  - Resolve:
    - current model/MLP/dataset revisions;
    - pinned MultiVSR source;
    - VTP checkpoint hash;
    - Romanian tokenizer.
  - Add:
    - `cloud/engine/src/backends/vsro_multivsr.py`;
    - `encode_video()`;
    - Romanian normalizer.
  - Acceptance: reproduce one pinned upstream Romanian sample and produce a
    normal evaluation report.
  - Evidence: `GitHub code pinned; dependent artifacts incomplete`

- [ ] **PT-013 — Build the LRRo-style generic representation probe**
  - Dependencies: PT-003, PT-012.
  - Add:
    - masked mean/max and attention pooling;
    - shared MLP classifier;
    - speaker/session-disjoint dataset loader;
    - top-1/top-5, macro F1, calibration, and confusion reporting.
  - Compare:
    - current Auto-AVSR;
    - LRS3;
    - VSRo;
    - personalized encoders.
  - Acceptance: identical probe configuration evaluates all encoders without
    changing sentence decoders.
  - Evidence: `TBD`

- [ ] **PT-014 — Run VSRo-to-English transfer**
  - Dependencies: PT-008, PT-009, PT-012, PT-013.
  - Compare:
    - frontend only;
    - frontend plus encoder;
    - frozen encoder probe;
    - partial unfreeze;
    - full unfreeze.
  - Acceptance: report shows zero-shot quality, convergence speed, final
    WER/CER, probe accuracy, memory, and trainable parameters.
  - Evidence: `TBD`

- [ ] **PT-015 — Reproduce pseudo-label scaling and OOD methodology**
  - Dependencies: PT-004, PT-008, PT-012.
  - Add:
    - teacher/pseudo-label provenance;
    - equal-hour human/pseudo subsets;
    - increasing pseudo-label scales;
    - speaker-seen/unseen and OOD cohorts;
    - OOV token/type metrics and run variance.
  - Acceptance: quality-at-fixed-hours is separated from benefit-from-more-data.
  - Evidence: `TBD`

## Paper-derived recognition improvements

- [ ] **PT-100 — VALLR phoneme + language-model branch**
  - Dependencies: PT-004, PT-011.
  - Paper: `2503.21408`.
  - Deliver:
    - phoneme target generation;
    - phoneme CTC model;
    - deterministic, n-gram, and language-model decoders;
    - raw phoneme and corrected-text outputs.
  - Acceptance: phoneme error and post-decoder WER are reported separately,
    including oracle-phoneme and hallucination controls.

- [ ] **PT-101 — Hearing Lips distillation branch**
  - Dependencies: PT-004, PT-011.
  - Paper: `1911.11502`.
  - Deliver:
    - pinned audio-teacher contract;
    - logit/CTC, feature, and combined losses;
    - shuffled/misaligned teacher negative control.
  - Acceptance: identical visual-only inference improves across repeated seeds;
    no audio dependency enters deployment.

- [ ] **PT-102 — SwinLip encoder branch**
  - Dependencies: PT-004, PT-013.
  - Paper: `2505.04394`.
  - Deliver:
    - encoder registry implementation;
    - parameter- and compute-matched comparisons;
    - ONNX/Core ML export investigation.
  - Acceptance: WER, RTF, memory, parameters, training throughput, and OOD
    results justify promotion or rejection.

- [ ] **PT-103 — External viseme decoder branch**
  - Dependencies: PT-100.
  - Paper: `2104.04784`.
  - Deliver:
    - published viseme mappings;
    - viseme CTC;
    - lexicon/n-gram/neural decoders;
    - viseme-confusion report.
  - Acceptance: raw viseme error and decoder contribution are measurable.

- [ ] **PT-104 — Multi-scale/multi-encoder branch**
  - Dependencies: PT-004, PT-102.
  - Paper: `2404.05466`.
  - Deliver:
    - mouth/lower-face or temporal-scale variants;
    - feature and late-fusion controls;
    - compute-matched comparison.
  - Acceptance: gains survive speaker-disjoint and OOD evaluation.

- [ ] **PT-105 — Multilingual knowledge branch**
  - Dependencies: PT-012, PT-100.
  - Papers: `2308.09311`, `2005.03846`.
  - Deliver:
    - shared encoder with language heads/adapters;
    - language-aware phoneme inventory;
    - simple sharing baseline before synchronous/bidirectional objectives.
  - Acceptance: low-resource gains are shown without hidden degradation to the
    established language.

- [ ] **PT-106 — Sequence-level objective branch**
  - Dependencies: PT-004, PT-011.
  - Paper: `2003.03983`.
  - Deliver:
    - policy-gradient objective plugin;
    - matched-extra-steps control;
    - reward variance and stability reporting.
  - Acceptance: repeated WER improvement is not explained by more training.

- [ ] **PT-107 — LipNet historical baseline**
  - Dependencies: PT-004.
  - Paper: `1611.01599`.
  - Deliver: bounded CTC reproduction with WER, parameters, RTF, and
    data-efficiency curve.
  - Acceptance: reproducible experiment-only backend.

## Paper-derived adjacent capabilities

- [ ] **PT-200 — LASER multi-face active-speaker selection**
  - Dependencies: PT-004.
  - Paper: `2501.11899`.
  - Deliver: face tracking, landmark/motion selection, oracle comparison.
  - Acceptance: downstream WER and selection accuracy beat simple largest-face
    and motion baselines.

- [ ] **PT-201 — Dataset synchronization/integrity QA**
  - Dependencies: PT-008.
  - Paper: `2401.15668`.
  - Deliver: controlled offset/drop/duplicate-frame tests and per-clip QA score.
  - Acceptance: corruption detection works without flagging intentional silent
    clips as invalid.

- [ ] **PT-202 — Wav2Lip augmentation study**
  - Dependencies: PT-008, PT-201.
  - Paper: `2008.10010`.
  - Deliver: real-only, mixed, and synthetic-pretrain arms with leakage checks.
  - Acceptance: real held-out performance improves; synthetic shortcuts and
    split contamination are ruled out.

- [ ] **PT-203 — Context-conditioned decoding**
  - Dependencies: PT-100.
  - Paper: `2504.15066`.
  - Deliver: no/correct/irrelevant/adversarial context arms and bounded
    vocabulary-bias control.
  - Acceptance: context-term recovery improves without unsupported insertions.

- [ ] **PT-204 — Lip-to-speech output track**
  - Dependencies: PT-100 and stable transcript/unit contracts.
  - Papers: `2306.03258`, `2502.12002`, `2303.00502`.
  - Deliver:
    - TTS baseline;
    - text/video-conditioned and direct-unit variants;
    - sync benchmark;
    - intelligibility, F0, duration, naturalness, and error-propagation reports.
  - Acceptance: separate package with synchronized, measurable output; no
    accidental coupling to transcription.

- [ ] **PT-205 — Dolphin audio-visual separation**
  - Dependencies: PT-100.
  - Paper: `2509.23610`.
  - Deliver: audio-only, continuous-visual, discrete-visual, oracle, and
    mismatched-face arms.
  - Acceptance: SI-SDR and separated-speech WER improve with target-speaker
    consistency.
