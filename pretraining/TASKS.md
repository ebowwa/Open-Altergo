# Pretraining and model research tasks

These tasks are separate from the iOS execution queue.

- [ ] **PT-001 — Pin and inspect the requested Hugging Face repository**
  - Resolve the full `main` commit for
    `simonlesaumon/lrs3-lipreader-visual-only`.
  - Review file history, sizes, serialization, architecture, tokenizer,
    preprocessing, checkpoint keys, and training provenance.
  - Download through the checked-in script and capture SHA-256 values.
  - Acceptance: `source.json` contains an immutable revision and complete,
    verified metadata; no weights are committed.
  - Evidence: `PARTIAL: model card supplied; Hub revision, complete inventory,
    sizes, hashes, full architecture commit, and serialization review remain`

- [ ] **PT-002 — Freeze the current Auto-AVSR evaluation baseline**
  - Dependencies: none.
  - Version text normalization and create speaker/session-disjoint manifests.
  - Record WER, CER, no-face rate, per-speaker distribution, real-time factor,
    peak memory, model size, and preprocessing failures.
  - Acceptance: one reproducible command emits metrics plus source/model/data
    revisions without exposing private clips.
  - Evidence: `TBD`

- [ ] **PT-003 — Evaluate the requested checkpoint as an isolated backend**
  - Dependencies: PT-001, PT-002.
  - Add an adapter only after architecture and serialization review.
  - Acceptance: identical held-out evaluation compares it to the frozen
    baseline; the current backend remains selectable and unchanged.
  - Evidence: `TBD`

- [ ] **PT-004 — Make VSRo-200 reproducible enough to test**
  - Resolve immutable Hub revisions and checksums for the sentence checkpoints,
    LRRo MLP heads, and dataset metadata.
  - Replace the upstream moving MultiVSR clone and unchecksummed VTP download
    with exact source and artifact pins in any reproduction environment.
  - Acceptance: every executable source and pickle artifact has a revision,
    inventory, checksum, provenance chain, and isolation decision; no upstream
    weights or datasets are committed.
  - Evidence: `PARTIAL: GitHub code pinned at
    267d44ee8fbd2de5b76a05441bb3bcbce838e457; model card pin recorded`

- [ ] **PT-005 — Add the English LRS3 backend adapter**
  - Dependencies: PT-001, PT-002.
  - Map checkpoint keys and tensor shapes to the current engine.
  - Implement backend selection through the shared service boundary.
  - Run the Adam demo through current and candidate backends.
  - Acceptance: Python API, HTTP API, and Gradio can select the candidate while
    the current backend remains the default; comparison artifacts include
    transcript, timings, failures, WER/CER where references exist, and latency.
  - Evidence: `TBD`

- [ ] **PT-006 — Warm-start Modal personalization from the LRS3 backend**
  - Dependencies: PT-005.
  - Compare frozen encoder, partial unfreeze, and full fine-tuning.
  - Acceptance: a real Modal run emits reloadable exported weights, run
    metadata, raw predictions, held-out WER/CER, and baseline comparison.
  - Evidence: `TBD`

- [ ] **PT-010 — Phoneme/viseme bottleneck experiment**
  - Dependencies: PT-002.
  - Reproduce the narrow claim shared by VALLR and external-viseme approaches.
  - Compare raw unit error and text WER with no LM, bounded LM, and LLM decoder.
  - Acceptance: raw visual and language-corrected results are reported
    separately on the same split.
  - Evidence: `TBD`

- [ ] **PT-011 — Speech-teacher distillation experiment**
  - Dependencies: PT-002.
  - Compare baseline, logits/CTC, intermediate-feature, and combined distillation
    while holding data, architecture, decoder, and steps constant.
  - Acceptance: evaluation pipeline has no audio input and the ablation records
    exact teacher/student revisions.
  - Evidence: `TBD`

- [ ] **PT-012 — Efficient visual encoder experiment**
  - Dependencies: PT-002.
  - Compare the current front end with a SwinLip-like candidate and only then a
    multi-scale candidate.
  - Acceptance: WER, latency, real-time factor, peak memory, parameters, model
    size, and export feasibility are reported.
  - Evidence: `TBD`

- [ ] **PT-013 — Reproduce VSRo supervision and robustness methodology**
  - Dependencies: PT-002, PT-004.
  - Compare human labels with pseudo-labels across matched data scales and
    preserve speaker-seen, speaker-unseen, and OOD evaluation.
  - Record OOV token/type rates and multiple-run variance alongside WER/CER.
  - Keep Romanian checkpoint results separate from English Open-Altergo results.
  - Acceptance: one controlled report attributes gains to label quality, data
    scale, and domain shift without changing normalization or decoder settings.
  - Evidence: `TBD`

- [ ] **PT-020 — Decide whether to open a lip-to-speech track**
  - Dependencies: PT-002.
  - Review LipVoicer, NaturalL2S, synchronization work, licensing, identity
    risks, consent, evaluation, and relationship to the product.
  - Acceptance: explicit go/no-go decision; no speech synthesis code enters the
    recognizer by accident.
  - Evidence: `TBD`
