# Visual speech research roadmap

## Scope and evidence level

This roadmap triages the supplied paper set for Open-Altergo. The initial pass
reviewed titles and abstracts, not every method appendix, code repository,
checkpoint, training split, or license. Reported results below remain paper
claims until reproduced under this repository's evaluation harness.

The primary product task is visual-only speech-to-text:

```text
silent face video ─► visual representation ─► linguistic units ─► text
```

Lip-to-speech, speech-to-lip generation, active-speaker detection, deepfake
detection, and audio-visual separation are related but different tasks. They
must not be counted as recognizer improvements.

## Research decisions

### P0 — investigate first

1. **Validate the requested Hugging Face candidate.**
   `simonlesaumon/lrs3-lipreader-visual-only` may offer a ready LRS3 checkpoint,
   but its revision, files, architecture, license, and provenance are unresolved.
   It stays inactive until those are pinned and reviewed.

2. **Phoneme-first decoding with an external language model.**
   [VALLR](https://huggingface.co/papers/2503.21408) proposes a Video
   Transformer with a phoneme CTC head followed by a fine-tuned LLM. Its abstract
   reports 18.7 WER on LRS3 while using much less labeled data than the compared
   approach. This is directly relevant to Open-Altergo because visually
   ambiguous phonemes should be resolved with explicit linguistic context,
   rather than hiding an unrestricted LLM correction inside evaluation.

3. **Cross-modal distillation during training.**
   [Hearing Lips](https://huggingface.co/papers/1911.11502) transfers
   multi-granularity knowledge from a speech recognizer into a visual model.
   Audio may be used as a teacher during authorized training while evaluation
   remains rigorously video-only. This could improve representations without
   changing the deployed input boundary.

4. **Efficient visual encoder.**
   [SwinLip](https://huggingface.co/papers/2505.04394) targets a lighter Swin
   Transformer visual speech encoder. Benchmark it against the current
   ResNet-3D front end for WER, real-time factor, memory, parameters, and export
   feasibility. Efficiency matters for Modal cost and the later Apple
   on-device track.

### P1 — controlled ablations

- [External viseme decoding](https://huggingface.co/papers/2104.04784):
  compare explicit video-to-viseme and viseme-to-text stages. The abstract
  reports a four-point WER improvement on LRS2 over its stated baseline.
- [Low-resource language transfer](https://huggingface.co/papers/2308.09311):
  separate general visual speech units from language-specific memory/decoding.
- [Synchronous bidirectional multilingual learning](https://huggingface.co/papers/2005.03846):
  test phoneme units and language-identity objectives only after the English
  baseline is stable.
- [Multi-scale video and multi-encoder](https://huggingface.co/papers/2404.05466):
  measure whether extra scales/encoders improve accuracy enough to justify
  compute and maintenance.

These methods should be individual experiment flags. Do not combine several
ideas in one run and then attribute the result to all of them.

### P2 — reference and historical baselines

- [LipNet](https://huggingface.co/papers/1611.01599) established end-to-end
  sentence-level CTC lip reading. It is useful as history and a conceptual
  baseline, not an expected modern production model.
- [Pseudo-Convolutional Policy Gradient](https://huggingface.co/papers/2003.03983)
  addresses teacher-forcing exposure bias and optimization mismatch with
  sequence-level objectives. Consider it only after simpler CTC/attention and
  phoneme objectives have clean baselines.

## Separate future output track

These papers synthesize speech from silent video:

- [LipVoicer](https://huggingface.co/papers/2306.03258) combines predicted text,
  video conditioning, diffusion, and ASR guidance.
- [NaturalL2S](https://huggingface.co/papers/2502.12002) uses differential DSP
  and F0 prediction for multi-speaker lip-to-speech.
- [Audio-visual synchronization for lip-to-speech](https://huggingface.co/papers/2303.00502)
  addresses dataset and generated-speech alignment.

That could later become:

```text
silent video ─► transcript/units ─► synchronized synthesized speech
```

It requires separate consent, voice identity policy, misuse analysis, audio
metrics, synchronization metrics, and human evaluation. It should not enter the
current transcription engine or iOS MVP.

[Wav2Lip](https://huggingface.co/papers/2008.10010) performs the reverse
operation—driving lip motion from speech. It may supply a synchronization
metric or carefully controlled augmentation study, but generated mouth motion
must never contaminate the held-out real-video test set.

## Adjacent work

- [Lips Are Lying](https://huggingface.co/papers/2401.15668) detects temporal
  audio/visual inconsistency in lip-sync deepfakes. It is relevant only if an
  audio-visual integrity or synthetic-data QA layer is added.
- [LASER](https://huggingface.co/papers/2501.11899) uses lip landmarks for robust
  active-speaker detection. It could help select the speaking face in multi-face
  video; the current single-face capture flow does not need it.
- [Chinese-LiPS](https://huggingface.co/papers/2504.15066) adds Chinese AVSR data
  and presentation-slide context. It informs a later multilingual/contextual
  track, not the English visual-only baseline.
- [Dolphin](https://huggingface.co/papers/2509.23610) performs audio-visual speech
  separation using discrete lip semantics and multi-scale attention. Its
  visual representations may be interesting, but the primary task depends on
  audio and must be evaluated separately.

## Reproducible experiment sequence

### R0 — freeze the baseline

- Pin the current Auto-AVSR model, tokenizer, preprocessing, detector, and code
  revision.
- Define one text-normalization implementation.
- Use speaker- and session-disjoint train, validation, and test manifests.
- Strip or ignore audio for every reported VSR evaluation.
- Record overall WER, CER, no-face rate, per-speaker WER distribution, real-time
  factor, peak memory, model size, and preprocessing failures.
- Record the Adam demo as qualitative regression evidence, never as the test set.

### R1 — admit or reject the requested checkpoint

1. Resolve the full Hugging Face commit.
2. Review the exact model card and declared license.
3. Inventory file names, sizes, Xet/LFS pointers, and SHA-256 values.
4. Determine architecture, tokenizer, crop size, frame rate, normalization, and
   expected detector/alignment.
5. Inspect serialized formats before loading. PyTorch pickle checkpoints are
   executable input and require a trusted provenance decision.
6. Create an isolated adapter behind a backend selector; do not overwrite the
   current engine.
7. Run identical held-out evaluation and publish the comparison, including
   failures and missing compatibility information.

### R2 — phoneme/viseme bottleneck

- Train or adapt a visual encoder to phoneme or viseme targets.
- Report phoneme/viseme error before adding a language model.
- Freeze that output and compare no LM, a bounded n-gram/finite decoder, and an
  LLM decoder.
- Report both raw visual output and post-language-model WER so linguistic
  correction cannot conceal a weak visual model.

### R3 — speech-teacher distillation

- Use audio only in the training teacher path.
- Compare no distillation, logits/CTC distillation, intermediate-feature
  distillation, and combined loss.
- Keep architecture, data, steps, and decoder constant across the ablation.
- Evaluate with audio physically absent from the input pipeline.

### R4 — visual encoder efficiency

- Compare the current ResNet-3D front end with SwinLip-like and multi-scale
  alternatives.
- Match parameter or compute budgets where possible.
- Measure preprocessing plus inference, not neural forward time alone.
- Export a candidate only after numerical parity and held-out quality checks.

### R5 — multilingual work

- Start only after the English split and evaluation are stable.
- Add language-explicit manifests, phoneme inventory provenance, and separate
  per-language metrics.
- Prevent translated or speaker-overlapping examples from leaking across splits.

## Promotion gate

A candidate becomes an Open-Altergo backend only when all of these are checked:

- immutable source revision and file checksums;
- compatible redistribution and use rights;
- documented original authors, datasets, and training stage;
- safe serialization review;
- deterministic preprocessing contract;
- held-out, speaker-disjoint visual-only metrics;
- latency, memory, and failure-rate comparison;
- integration and regression tests;
- no degradation hidden by a changed text normalizer or language model; and
- model card updated with actual limitations.

Until then it remains research metadata under `pretraining/`, not a supported
engine dependency.
