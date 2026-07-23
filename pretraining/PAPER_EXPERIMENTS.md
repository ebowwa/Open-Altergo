# Paper-to-capability experiment map

This document converts every supplied paper into a concrete Open-Altergo
experiment. The paper summaries currently come from title/abstract-level
triage. Before reproducing an experiment, read the full paper, appendices,
official code, data split, and hyperparameters. Do not invent missing method
details from this plan.

## 1. Priority map

| ID | Paper or source | Capability branch | Priority | First deliverable |
| --- | --- | --- | --- | --- |
| 2303.08807 | Auto-AVSR | baseline | M0 | freeze current reproduction contract |
| HF-LRS3 | LRS3 visual-only model | backend | M1 | selectable English backend |
| 2607.08112 | VSRo-200 | supervision/transfer | M3 | English transfer and OOD methodology |
| 2503.21408 | VALLR | phoneme + LM | P0 | raw phoneme versus LM-corrected report |
| 1911.11502 | Hearing Lips | distillation | P0 | audio-teacher ablation |
| 2505.04394 | SwinLip | efficient encoder | P0 | WER/latency/memory comparison |
| 2104.04784 | External viseme decoding | unit bottleneck | P1 | viseme error and text WER |
| 2308.09311 | Low-resource language transfer | multilingual transfer | P1 | shared encoder/language head ablation |
| 2005.03846 | Synchronous bidirectional multilingual learning | multilingual units | P1 | phoneme/language objective ablation |
| 2404.05466 | Multi-scale video and multi-encoder | visual encoder | P1 | compute-matched multi-scale comparison |
| 2003.03983 | Pseudo-Convolutional Policy Gradient | sequence objective | P2 | objective-only training ablation |
| 1611.01599 | LipNet | historical baseline | P2 | small reproducible CTC baseline |
| 2501.11899 | LASER | active speaker | adjacent | multi-face speaker selection benchmark |
| 2401.15668 | Lips Are Lying | integrity/QA | adjacent | sync/integrity diagnostic |
| 2008.10010 | Wav2Lip | synthetic data/sync | adjacent | augmentation contamination study |
| 2504.15066 | Chinese-LiPS | context/multilingual | future | context-conditioned decoder prototype |
| 2306.03258 | LipVoicer | lip-to-speech | separate output | text/video-conditioned speech prototype |
| 2502.12002 | NaturalL2S | lip-to-speech | separate output | F0/naturalness experiment |
| 2303.00502 | AV sync for lip-to-speech | output evaluation | separate output | synchronization benchmark |
| 2509.23610 | Dolphin | AV separation | separate multimodal | visual-semantic separation prototype |

## 2. Shared experiment rules

Every experiment gets:

```text
experiment ID
paper revision and code revision
baseline bundle
dataset fingerprint
preprocessing revision
seed
changed variable
held-constant variables
raw predictions
summary metrics
compute/latency/memory
decision
```

The first run changes one capability at a time. For example, VALLR's unit head
and language model must not arrive in the same comparison as a new Swin visual
encoder. Otherwise a WER change cannot be attributed.

Use the same:

- train/validation/test manifests;
- text normalizer;
- face detector and crop contract unless preprocessing is the variable;
- decoding beam and language model unless decoding is the variable;
- seeds and training-step budget;
- failure accounting.

## 3. Baseline and model-source experiments

### EXP-BASE-001 — Auto-AVSR reproduction

Source:
[Auto-AVSR: Audio-Visual Speech Recognition with Automatic Labels](https://arxiv.org/abs/2303.08807)

Capability:

- establish the exact architecture, preprocessing, tokenizer, and decoding
  contract already used by Open-Altergo;
- separate reproduced behavior from changes inherited through re-hosted weights.

Implementation:

- inventory `E2E`, ResNet-3D frontend, Conformer encoder, Transformer decoder,
  CTC head, SentencePiece vocabulary, and beam-search weights;
- record tensor shapes and total parameters;
- export current preprocessing as a `PreprocessingSpec`;
- add fixed input/output fixtures;
- compare the current mirror checkpoint against any official checkpoint that
  can be pinned.

Experiment:

- run the frozen current backend on the held-out English manifest;
- record greedy, CTC-only, attention-only, and joint decoding;
- sweep only beam size and CTC weight after the default is frozen.

Metrics:

- WER/CER, exact match, RTF, memory, no-face rate;
- raw N-best diversity;
- effect of segmentation versus whole-clip decoding.

Decision:

- this remains the control backend even if another model wins.

### EXP-SRC-001 — LRS3 visual-only checkpoint

Source:
[`simonlesaumon/lrs3-lipreader-visual-only`](https://huggingface.co/simonlesaumon/lrs3-lipreader-visual-only)

Capability:

- a second English visual-only initialization;
- possible closer reproduction of Adam's launch demo;
- possible stronger starting point for personal fine-tuning.

Implementation and acceptance are specified in Phase 1 of
`CAPABILITY_PLAN.md`.

Experiment:

- current versus LRS3 on identical preprocessing where compatible;
- upstream preprocessing versus current preprocessing as a separate 2x2
  ablation;
- base versus personalized from both initializations.

Decision:

- support if it gives a quality or efficiency advantage and remains maintainable
  through the shared backend contract;
- keep only as initialization if it helps fine-tuning but not zero-shot use.

### EXP-SRC-002 — VSRo-200 sentence model

Source:
[VSRo-200](https://arxiv.org/abs/2607.08112)

Capability:

- Romanian sentence transcription;
- a low-resource transfer initialization;
- pseudo-label scaling, OOD, and speaker split methodology;
- encoder representations for LRRo-style probes.

Implementation:

- dedicated MultiVSR/VTP backend;
- Romanian tokenizer and normalizer;
- `encode_video()` support;
- English decoder replacement/transfer path;
- dataset cohort fields described in Phase 3.

Experiment:

- reproduce one Romanian sample;
- compare VSRo frontend-only, full encoder, and frozen-probe transfer;
- reproduce equal-hour human/pseudo supervision comparisons;
- add seen/unseen and OOD reports.

Decision:

- sentence backend remains language-specific;
- promote transfer components only if they improve English learning speed,
  held-out WER, or representation-probe results.

## 4. Linguistic-unit and decoder capabilities

### EXP-LANG-001 — VALLR phoneme-to-language-model decoding

Paper:
[VALLR: Visual ASR Language Model for Lip Reading](https://huggingface.co/papers/2503.21408)

Capability:

- make the visual model predict phonemes or other speech units;
- use a separate language model to resolve visually ambiguous sequences;
- expose raw visual evidence separately from linguistic correction.

Hypothesis:

The current 5,000-unit SentencePiece decoder forces the visual encoder and
language model behavior into one model. A phoneme bottleneck may be easier to
learn from limited personal data, while a separate LM can improve readable
text.

Modules:

```text
cloud/engine/src/units/phonemes.py
cloud/engine/src/units/alignment.py
cloud/engine/src/decoding/phoneme_ctc.py
cloud/engine/src/decoding/language_model.py
training/experiments/train_phoneme_ctc.py
```

Data:

- derive phoneme targets from transcripts using a pinned grapheme-to-phoneme
  model;
- retain word/phoneme boundaries and conversion failures;
- manually audit names, acronyms, slang, and homographs;
- do not use test references as LM prompts.

Experiment arms:

| Arm | Visual output | Text decoder |
| --- | --- | --- |
| A | current subwords | current joint decoder |
| B | phoneme CTC | deterministic lexicon/beam |
| C | phoneme CTC | bounded n-gram LM |
| D | phoneme CTC | fine-tuned language model |
| E | oracle phonemes | each decoder |

Metrics:

- phoneme error rate before text decoding;
- WER/CER after each decoder;
- oracle-phoneme WER to isolate LM limitations;
- hallucination rate where text contains unsupported words;
- named-entity accuracy;
- latency and LM compute.

Required result schema:

```json
{
  "visual_units": ["HH", "EH", "L", "OW"],
  "visual_unit_scores": [],
  "raw_unit_error_rate": 0.0,
  "decoded_text": "hello",
  "decoder_id": "phoneme-lm-v1"
}
```

Decision:

- proceed only if raw phoneme quality is competitive and LM gains do not come
  from unconstrained hallucination;
- always return raw units in evaluation artifacts.

### EXP-LANG-002 — external viseme decoding

Paper:
[Lip reading using external viseme decoding](https://huggingface.co/papers/2104.04784)

Capability:

- explicit visual-unit vocabulary based on mouth-shape equivalence;
- independently replaceable viseme-to-text decoder;
- diagnostics showing which visual distinctions are impossible or weak.

Modules:

```text
cloud/engine/src/units/visemes.py
cloud/engine/src/decoding/viseme_lexicon.py
training/experiments/train_viseme_ctc.py
```

Experiment:

- define at least two published phoneme-to-viseme maps;
- compare phoneme, viseme, character, and SentencePiece targets with the same
  encoder;
- report unit error before external decoding;
- evaluate deterministic lexicon, n-gram, and neural decoder separately.

Metrics:

- viseme error rate;
- phoneme-pair confusion collapsed and uncollapsed;
- word WER;
- ambiguity set size per decoded word;
- decoder hallucination/substitution types.

Decision:

- use visemes as an auxiliary loss or diagnostic if text WER does not improve;
- promote as primary units only if the external decoder adds reproducible value.

### EXP-LANG-003 — sequence-level policy-gradient objective

Paper:
[Pseudo-Convolutional Policy Gradient for Sequence-to-Sequence Lip-Reading](https://huggingface.co/papers/2003.03983)

Capability:

- optimize a sequence-level reward closer to WER;
- reduce exposure bias from teacher-forced decoder training.

Implementation:

- add a training objective plugin, not a new backend;
- reproduce the paper's exact reward/baseline after full-paper review;
- log reward variance and gradient norms;
- retain cross-entropy/CTC warm start.

Experiment:

| Arm | Objective |
| --- | --- |
| A | current joint CTC/attention |
| B | current + sequence-level objective after warm-up |
| C | matched-step additional cross-entropy control |

Metrics:

- WER/CER, training stability, reward variance;
- decode length and repetition;
- wall-clock cost per optimizer step.

Decision:

- stop if gains are explained by extra training steps or unstable across seeds.

## 5. Cross-modal supervision capabilities

### EXP-DISTILL-001 — Hearing Lips

Paper:
[Hearing Lips: Improving Lip Reading by Distilling Speech Recognizers](https://huggingface.co/papers/1911.11502)

Capability:

- use audio only during training as a stronger teacher;
- deploy the same visual-only input path;
- transfer logits and intermediate speech representations.

Modules:

```text
training/distillation/teachers.py
training/distillation/losses.py
training/experiments/train_distilled_vsr.py
```

Teacher contract:

```text
audio -> time-aligned logits/features
video -> student logits/features
alignment mask -> loss
```

Experiment arms:

- no teacher;
- output-logit/CTC distillation;
- intermediate-feature distillation;
- both;
- shuffled/misaligned teacher negative control.

Hold constant:

- student architecture;
- video examples;
- optimizer steps;
- decoder;
- test input with audio physically absent.

Metrics:

- raw visual WER/CER;
- representation similarity;
- improvement by noise/articulation cohort;
- teacher preprocessing cost;
- behavior when audio transcript disagrees with visible articulation.

Decision:

- promote the training recipe if gains remain when deployment has no audio;
- never add a hidden audio dependency to inference.

### EXP-SUP-001 — pseudo-label scaling

Primary source:
[VSRo-200](https://arxiv.org/abs/2607.08112), with Auto-AVSR as foundational
context.

Capability:

- expand training data using automatically generated transcriptions;
- quantify when more noisy labels beat fewer human labels.

Implementation:

- teacher registry and revision;
- pseudo-label JSONL with raw/normalized text and filters;
- matched-hour subset generator;
- confidence and disagreement analysis;
- human correction overlay without destroying original teacher output.

Experiment:

- human versus pseudo at matched hours;
- increasing pseudo hours;
- filtered versus unfiltered pseudo labels;
- current ASR teacher versus a stronger teacher;
- voiced training video versus silent-only evaluation.

Metrics:

- WER/CER by hours;
- label disagreement rate;
- OOV rates;
- retained/rejected hours;
- cost per usable hour;
- variance across data shuffles.

Decision:

- choose a filtering threshold from validation only;
- report both quality-at-fixed-hours and scalability.

## 6. Visual encoder capabilities

### EXP-ENC-001 — SwinLip

Paper:
[SwinLip: An Efficient Visual Speech Encoder for Lip Reading Using Swin Transformer](https://huggingface.co/papers/2505.04394)

Capability:

- replace or augment the ResNet-3D frontend with a more efficient visual encoder;
- improve Modal throughput and possible future Apple deployment.

Modules:

```text
cloud/engine/src/encoders/swinlip.py
cloud/engine/src/encoders/registry.py
training/experiments/train_encoder_variant.py
```

Experiment:

- current ResNet-3D frontend;
- SwinLip-like encoder at matched parameters;
- Swin encoder at matched FLOPs;
- frozen decoder versus end-to-end retraining.

Metrics:

- WER/CER;
- frontend and total RTF;
- peak memory;
- parameter count and approximate FLOPs;
- training throughput;
- export to ONNX/Core ML feasibility;
- quality under resolution, lighting, and pose shifts.

Decision:

- promote if it improves quality or materially reduces compute within an
  explicitly accepted quality delta;
- do not compare only neural forward time—include face preprocessing.

### EXP-ENC-002 — multi-scale video and multi-encoder

Paper:
[Enhancing Lip Reading with Multi-Scale Video and Multi-Encoder](https://huggingface.co/papers/2404.05466)

Capability:

- combine local mouth detail with broader facial/contextual motion;
- test whether several temporal/spatial scales resolve articulation ambiguity.

Implementation candidates:

- 88x88 mouth stream plus 160x160 lower-face stream;
- short-frame-rate/high-detail plus long-context/lower-rate stream;
- encoder fusion before decoder;
- late logit fusion as a lower-complexity control.

Experiment:

| Arm | Streams | Fusion |
| --- | --- | --- |
| A | current mouth | none |
| B | larger single crop | none |
| C | two scales | shared encoder |
| D | two scales | separate encoders + feature fusion |
| E | two scales | late logit fusion |

Metrics:

- WER/CER;
- compute and memory;
- face-detection sensitivity;
- gains by pose and resolution;
- whether wider crops learn speaker/background shortcuts.

Decision:

- require gains under compute-matched and speaker-disjoint evaluation.

### EXP-HIST-001 — LipNet baseline

Paper:
[LipNet: End-to-End Sentence-level Lipreading](https://huggingface.co/papers/1611.01599)

Capability:

- a simpler CTC sentence baseline;
- an interpretable reference for whether complexity is buying capability.

Implementation:

- reproduce on a bounded dataset/config;
- use the same evaluation normalizer;
- expose as experiment-only backend.

Metrics:

- WER/CER, parameters, training time, RTF;
- data-efficiency curve.

Decision:

- keep as historical/regression baseline, not expected production default.

## 7. Multilingual and contextual capabilities

### EXP-MULTI-001 — low-resource language knowledge separation

Paper:
[Lip Reading for Low-resource Languages by Learning and Combining General Speech Knowledge and Language-specific Knowledge](https://huggingface.co/papers/2308.09311)

Capability:

- shared visual speech encoder;
- language-specific memory/decoder components;
- faster addition of low-resource languages or personal vocabularies.

Architecture:

```text
video -> shared visual encoder
      -> language adapter/memory
      -> language-specific decoder/head
```

Experiment:

- English only;
- Romanian only;
- shared encoder with separate heads;
- shared encoder plus lightweight language adapters;
- full multilingual decoder with language token.

Metrics:

- per-language WER/CER;
- transfer gain at 1h/5h/10h/25h;
- negative transfer;
- added parameters per language;
- catastrophic forgetting.

Decision:

- promote only if low-resource learning improves without materially degrading
  the established language.

### EXP-MULTI-002 — synchronous bidirectional multilingual learning

Paper:
[Synchronous Bidirectional Learning for Multilingual Lip Reading](https://huggingface.co/papers/2005.03846)

Capability:

- align shared visual/phonetic representations across languages;
- use bidirectional or mutual learning objectives to improve language transfer.

Implementation:

- exact objectives must be transcribed from the full paper;
- add them as loss plugins;
- use phoneme inventories with explicit language provenance;
- distinguish universal and language-specific phonemes.

Experiment:

- separate monolingual models;
- simple shared encoder;
- shared encoder plus synchronous/bidirectional objective;
- shuffled-language negative control.

Metrics:

- per-language WER and phoneme error;
- cross-language retrieval/similarity;
- low-resource sample efficiency;
- negative transfer.

Decision:

- proceed only after the simple shared-encoder baseline is stable.

### EXP-CONTEXT-001 — Chinese-LiPS presentation context

Paper:
[Chinese-LiPS: A Chinese audio-visual speech recognition dataset with Lip-reading and Presentation Slides](https://huggingface.co/papers/2504.15066)

Capability:

- condition decoding on explicit visual/textual context such as slides, app UI,
  document vocabulary, or user-provided phrase sets;
- later multilingual Chinese evaluation.

Open-Altergo adaptation:

```text
lip video -> visual units
context document/UI OCR -> candidate terms/embeddings
decoder -> context-biased text
```

Experiment:

- no context;
- correct context;
- irrelevant context negative control;
- adversarial context containing plausible but unspoken words;
- bounded vocabulary bias versus free-form LLM correction.

Metrics:

- WER overall and on context terms;
- hallucinated-context insertion rate;
- OOV recovery;
- latency.

Decision:

- context must help spoken terms without causing unsupported insertions.

## 8. Speaker selection, integrity, and synthetic-data capabilities

### EXP-FRONT-001 — LASER active-speaker detection

Paper:
[LASER: Lip Landmark Assisted Speaker Detection for Robustness](https://huggingface.co/papers/2501.11899)

Capability:

- select the speaking face in multi-person video;
- reject non-speaking faces before VSR;
- use landmarks/mouth dynamics as robust cues.

Modules:

```text
cloud/engine/src/frontends/face_tracks.py
cloud/engine/src/frontends/active_speaker.py
```

Experiment:

- current largest/first detected face;
- motion-energy selection;
- LASER-like landmark-assisted selection;
- oracle face track.

Metrics:

- active-speaker selection accuracy;
- downstream WER;
- track switches;
- no-speaker false positives;
- latency with 1, 2, 4, and 8 faces.

Decision:

- keep out of the single-person MVP path until multi-face inputs are supported;
- use it when selection errors dominate downstream WER.

### EXP-QA-001 — Lips Are Lying integrity diagnostics

Paper:
[Lips Are Lying](https://huggingface.co/papers/2401.15668)

Capability:

- detect temporal audio/visual inconsistency;
- audit voiced training recordings and synthetic augmentation;
- flag likely desynchronization before training.

Implementation:

- QA command over dataset manifests;
- frame/audio offset sweep;
- per-clip sync score and exclusion reason;
- no dependency in silent-only inference.

Experiment:

- original clips;
- known ±40/80/120/200 ms offsets;
- dropped/duplicated frames;
- dubbed or unrelated audio;
- silent clips as a separate expected category.

Metrics:

- offset detection error;
- AUROC for corrupted versus aligned voiced clips;
- false alarms on intentionally silent clips.

Decision:

- use as dataset QA if it reliably catches corruption; do not call it a
  lip-reading improvement.

### EXP-SYN-001 — Wav2Lip augmentation

Paper:
[A Lip Sync Expert Is All You Need for Speech to Lip Generation In The Wild](https://huggingface.co/papers/2008.10010)

Capability:

- generate controlled mouth-motion variants;
- test a synchronization metric;
- augment rare phrases or visual conditions.

Risks to measure technically:

- synthetic artifacts become shortcuts;
- speaker identity leakage;
- exact text duplicates cross into validation/test;
- recognizer improves on synthetic but degrades on real video.

Experiment:

- real-only training;
- real plus 10/25/50% synthetic;
- synthetic pretraining then real fine-tuning;
- matched extra-real-data control;
- synthetic-only held-out diagnostic, never primary result.

Metrics:

- real-video WER/CER;
- synthetic-versus-real domain classifier accuracy;
- representation shift;
- synchronization score;
- phrase/speaker leakage checks.

Decision:

- use only if real held-out performance improves and leakage checks pass.

## 9. Lip-to-speech output capabilities

These experiments form a separate output package. They do not modify the
transcription backend until explicitly connected through a stable transcript or
unit contract.

Proposed future path:

```text
cloud/engine/src/lip_to_speech/
├── base.py
├── text_conditioned.py
├── direct_units.py
├── synchronization.py
└── evaluation.py
```

### EXP-L2S-001 — LipVoicer

Paper:
[LipVoicer: Generating Speech from Silent Videos Guided by Lip Reading](https://huggingface.co/papers/2306.03258)

Capability:

- synthesize speech from silent video using predicted text and video
  conditioning;
- compare transcript-mediated output with direct visual conditioning.

Experiment:

- transcript-to-TTS baseline;
- transcript plus video-conditioned model;
- oracle transcript plus video;
- predicted transcript plus video;
- video without transcript where supported.

Metrics:

- ASR intelligibility/WER of synthesized speech;
- lip/audio synchronization;
- speaker similarity only when explicitly intended;
- MOS or human naturalness;
- error propagation from incorrect lip reading.

Decision:

- keep downstream of transcription until it demonstrably adds timing/prosody
  value beyond ordinary TTS.

### EXP-L2S-002 — NaturalL2S

Paper:
[NaturalL2S](https://huggingface.co/papers/2502.12002)

Capability:

- more natural multi-speaker lip-to-speech;
- explicit F0/prosody prediction and differential DSP components.

Experiment:

- text-to-TTS baseline;
- LipVoicer-style output;
- NaturalL2S-style direct output;
- oracle versus predicted text/units;
- seen versus unseen speakers.

Metrics:

- intelligibility;
- F0 correlation and voiced/unvoiced accuracy;
- duration/rhythm error;
- sync;
- naturalness and speaker similarity.

Decision:

- only proceed after a stable synchronized baseline exists.

### EXP-L2S-003 — audio-visual synchronization evaluation

Paper:
[On the Audio-visual Synchronization for Lip-to-Speech Synthesis](https://huggingface.co/papers/2303.00502)

Capability:

- define the synchronization benchmark for generated speech;
- prevent intelligible but visibly mistimed output from passing.

Implementation:

- offset-sensitive sync metric;
- phoneme/viseme alignment report;
- frame-level lag visualization;
- controlled temporal-shift test set.

Metrics:

- mean/median absolute offset;
- sync confidence;
- intelligibility versus synchronization tradeoff.

Decision:

- this becomes a required evaluation layer for every lip-to-speech model.

## 10. Audio-visual separation capability

### EXP-SEP-001 — Dolphin

Paper:
[Efficient Audio-Visual Speech Separation with Discrete Lip Semantics and Multi-Scale Global-Local Attention](https://huggingface.co/papers/2509.23610)

Capability:

- isolate a target speaker from mixed audio using lip semantics;
- test whether discrete visual units learned for VSR improve separation.

Architecture:

```text
target lip video -> discrete visual semantics
mixed audio + visual semantics -> separated target audio
```

Experiment:

- audio-only separator;
- continuous visual features;
- discrete phoneme/viseme features from Open-Altergo;
- oracle visual units;
- mismatched-face negative control.

Metrics:

- SI-SDR/SDR improvement;
- separated-speech ASR WER;
- target-speaker consistency;
- failure under visual/audio mismatch;
- latency.

Decision:

- keep as a separate multimodal backend; reuse representations only if the
  direct VSR work produces stable visual units.

## 11. Dependency order

```text
Auto-AVSR frozen baseline
  ├── LRS3 backend
  │    └── personal fine-tuning comparison
  ├── VSRo backend
  │    ├── pseudo-label scaling
  │    ├── multilingual transfer
  │    └── LRRo-style probes
  ├── phoneme/viseme units
  │    ├── VALLR language model
  │    ├── multilingual objectives
  │    └── Dolphin separation
  ├── visual encoder registry
  │    ├── SwinLip
  │    └── multi-scale/multi-encoder
  ├── dataset QA
  │    ├── Lips Are Lying
  │    └── Wav2Lip augmentation
  └── stable transcript/unit output
       ├── LipVoicer
       ├── NaturalL2S
       └── synchronization benchmark
```

LASER branches from preprocessing once multi-face capture is in scope.
Chinese-LiPS context work branches from the language-model decoder after raw
visual outputs are exposed.

## 12. Recommended execution queue

1. `EXP-BASE-001`: freeze evaluator and current backend.
2. `EXP-SRC-001`: load the LRS3 checkpoint and run Adam comparison.
3. LRS3/current personalization matrix on Modal.
4. `EXP-SRC-002`: implement VSRo and encoder transfer.
5. generic LRRo-style representation probe.
6. `EXP-LANG-001`: phoneme CTC with raw-unit reporting.
7. `EXP-DISTILL-001`: audio-teacher distillation.
8. `EXP-ENC-001`: SwinLip compute/quality comparison.
9. `EXP-LANG-002`: viseme bottleneck.
10. `EXP-ENC-002`: multi-scale visual input.
11. multilingual objectives and contextual decoding.
12. dataset QA and synthetic augmentation.
13. lip-to-speech and separation only after the input/representation work is
    stable.

This queue prioritizes capabilities that directly improve silent English
transcription and personalization before adjacent multimodal outputs.
