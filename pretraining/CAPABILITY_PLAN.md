# Model capability plan

The immediate goal is not to collect model cards. It is to determine which
upstream work can improve Open-Altergo and then make those capabilities
selectable in the engine.

## Capability matrix

| Capability | LRS3 visual-only checkpoint | VSRo sentence model | LRRo MLP heads |
| --- | --- | --- | --- |
| Reproduce Adam-style English demo | Primary candidate | No; Romanian decoder | No; isolated words |
| Warm-start personal fine-tuning | High-value experiment | Encoder-transfer experiment | No |
| Visual-only sentence transcription | Yes, after adapter work | Romanian only | No |
| Better visual representation | Likely | Worth transfer ablation | Probe only |
| Pseudo-label training methodology | Training recipe reference | Strong reference | No |
| OOD/speaker evaluation design | Limited card evidence | Strong reference | Domain-transfer probe |
| Direct Apple integration | Through Python/HTTP API | Through Python/HTTP API | Not an app backend |

## CAP-001 — Load the English LRS3 checkpoint

1. Resolve its full Hugging Face revision and inventory.
2. Download `model_avg_10.pth` into the ignored cache and compute its checksum.
3. Inspect the checkpoint keys without importing arbitrary upstream modules.
4. Diff its tensor names and shapes against the current Auto-AVSR engine.
5. Implement an isolated backend adapter rather than replacing the existing
   backend.
6. Reproduce the exact mouth-crop, frame-rate, normalization, chunking,
   vocabulary, and decoding contract.
7. Run the Adam launch video through both backends and save transcripts,
   segment timings, preprocessing failures, and latency.

Deliverable: `--backend lrs3-visual-only` works through the Python API, HTTP API,
and Gradio without changing the existing default.

## CAP-002 — Warm-start Modal personalization

1. Add the LRS3 backend as an optional initialization checkpoint for the Modal
   trainer.
2. Validate full-model, decoder-only, and visual-encoder-plus-decoder fine-tuning
   modes.
3. Train on one personal dataset with speaker-disjoint validation.
4. Emit `last.ckpt`, averaged/exported weights, run metadata, raw validation
   predictions, WER/CER, and a comparison against the unfine-tuned checkpoint.
5. Confirm the exported personalized model loads through every interface.

Deliverable: one command performs a real Modal fine-tune and produces a
measurably evaluated backend.

## CAP-003 — Extract VSRo-200 techniques

Do not treat Romanian output as an English demo. Use the source for capabilities
that transfer:

1. Reproduce its human-label versus pseudo-label data-scaling experiment.
2. Port its speaker-seen, speaker-unseen, and OOD manifest structure.
3. Add OOV token/type rates and run variance to Open-Altergo evaluation.
4. Test the Romanian visual encoder as a frozen feature extractor on English
   personal data.
5. Compare frozen probe, partial unfreeze, and full fine-tune.

Deliverable: a controlled transfer report showing whether VSRo pretraining
improves English personalization speed or accuracy.

## CAP-004 — Use LRRo heads as a probe pattern

The MLP heads themselves do not provide sentence transcription. Their useful
capability is the experiment pattern:

1. freeze a sentence-level visual encoder;
2. pool its temporal representations;
3. train a lightweight classifier;
4. measure how separable visual word representations are across domains.

Implement the probe generically so it can diagnose current, LRS3, and VSRo
encoders on the same authorized word-clip set.

Deliverable: an encoder-comparison command that reports top-1/top-5 accuracy and
confusion matrices without modifying the transcription decoder.

## Required backend boundary

Every experiment backend must expose the same engine contract:

```text
video path
  -> validated preprocessing
  -> visual encoder
  -> decoder
  -> transcript + segments + diagnostics
```

The Python API, HTTP API, Gradio app, Modal trainer, and future Apple clients
must select a backend by configuration. No interface should import model
implementation details directly.

## Distribution checkpoint

Licensing and redistribution are packaging concerns, not blockers for the local
capability work above. Before publishing weights, bundling a model in an app, or
offering a commercial hosted backend, perform the separate distribution review.
