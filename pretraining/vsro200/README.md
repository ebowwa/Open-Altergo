# VSRo-200 research sources

This directory catalogs the VSRo-200 code, dataset metadata, sentence-level
Romanian checkpoints, and LRRo classifier heads. It does not vendor any of
them, and none is an active Open-Altergo backend.

## Why it is relevant

VSRo-200 is useful as a research reference for:

- scaling human labels against Whisper pseudo-labels;
- speaker-seen versus speaker-unseen evaluation;
- out-of-distribution sets for vlogs, specialized language, noisy video, and
  archival footage;
- gender-controlled split analysis;
- transfer from sentence-level VSR representations to isolated-word
  classification; and
- shallow audio/visual fusion under acoustic noise.

It is not a drop-in replacement for the English silent-speech demo. The released
sentence model and tokenizer are Romanian, while the LRRo artifacts are word
classifiers rather than sentence transcribers. Its immediate value is encoder
transfer, pseudo-label scaling, OOD evaluation, and probe design.

## Source status

The full machine-readable record is in [`sources.json`](sources.json).

| Source | Pin | License | Status |
| --- | --- | --- | --- |
| `vsro200/vsro200` GitHub code | `267d44ee8fbd2de5b76a05441bb3bcbce838e457` | Inspect architecture and training |
| `vsro200/models-vsro200` | `4195b93fb621b2911fd2d854ca46eea054c735dd` | Inventory, download, and test encoder transfer |
| `vsro200/mlp-lrro-vsro200` | Unresolved | Resolve revision, then reproduce probe pattern |
| `vsro200/vsro200` dataset | Unresolved | Reproduce supervision/OOD methodology |

The known model pin is an immutable, indexed Hugging Face revision that follows
the commit which added CC-BY-NC-4.0 metadata. It is not asserted to be the
current default branch. A later promotion must inventory every file and capture
SHA-256 values.

## Upstream reproducibility gaps

The pinned GitHub repository includes methodology and training scripts, but its
root contains no `LICENSE` file. Its setup script also:

- shallow-clones the moving default branch of MultiVSR;
- copies source and tokenizer files out of that checkout;
- downloads an approximately 1 GB VTP PyTorch checkpoint from VGG Oxford; and
- verifies neither dependency by revision nor checksum.

Its inference code downloads `.pt` files without a `revision=` argument and
loads them with `torch.load`. Treat every checkpoint as executable input.
Reproduction in Open-Altergo must replace those moving downloads with explicit
pins, hashes, and isolated loading.

## Download for inspection

Pass a source alias and full 40-character Hub commit:

```bash
pretraining/vsro200/download.sh models <commit-sha>
pretraining/vsro200/download.sh mlp <commit-sha>
pretraining/vsro200/download.sh dataset <commit-sha>
```

Downloads go under ignored `pretraining/.cache/vsro200/` directories and receive
a generated `SHA256SUMS`. Do not commit weights, datasets, Hugging Face caches,
or LRRo material.

## Evaluation boundary

Use VSRo-200 to design experiments, not to claim English accuracy. Any run must
keep language, tokenizer, data rights, text normalization, speaker split,
checkpoint revision, and post-decoder correction explicit. The Adam launch
video remains qualitative regression material, never training data or a test
set.

The concrete implementation order is in
[`../CAPABILITY_PLAN.md`](../CAPABILITY_PLAN.md).
