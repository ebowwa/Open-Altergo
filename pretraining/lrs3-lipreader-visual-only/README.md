# LRS3 visual-only Auto-AVSR candidate

Upstream:
[`simonlesaumon/lrs3-lipreader-visual-only`](https://huggingface.co/simonlesaumon/lrs3-lipreader-visual-only)

This entry records the requested Hugging Face repository without committing its
weights. Its model card was supplied for review, resolving the architecture,
training recipe, intended use, and declared license. The immutable Hub revision,
complete file inventory, sizes, and checksums remain unresolved.

## Current status

| Field | Status |
| --- | --- |
| Repository type | Hugging Face model repository |
| Immutable revision | Unresolved |
| Expected checkpoint | `model_avg_10.pth`; size and checksum unresolved |
| Architecture/config | Visual-only Auto-AVSR, reported architecture commit `182b628` |
| License | CC-BY-NC-4.0; noncommercial research only |
| Training data | `Ainncy/LRS3` trainval, with a deterministic 98/2 holdout |
| Reported training | 20 epochs, A100-80GB, LR 0.001, approximately 4h40 |
| Open-Altergo compatibility | Not tested |
| Active in training or inference | No |

This is a fine-tuned English checkpoint, not a generic pretraining artifact.
The reported validation numbers use a held-out portion of `trainval`, because
the official LRS3 test set is not distributed by `Ainncy/LRS3`. Do not compare
those numbers directly with published official-test results.

The upstream card also states that the original videos, mouth crops, and
transcriptions are not redistributed and must not be redistributed without
authorization from the dataset copyright holders.

## Compatibility contract to verify

- video-only, 250M-parameter end-to-end Auto-AVSR;
- MediaPipe face detection and mouth ROI extraction;
- 16-second preprocessing segments;
- exact crop size, frame rate, normalization, vocabulary, and decoder settings
  still need to be read from the pinned code and checkpoint;
- `model_avg_10.pth` is a pickle-capable PyTorch checkpoint and must be reviewed
  as executable input before loading.

## Pin and download on a connected machine

Resolve the upstream `main` commit:

```bash
git ls-remote \
  https://huggingface.co/simonlesaumon/lrs3-lipreader-visual-only \
  refs/heads/main
```

Review the file tree, file sizes, Git/Xet history, and model card at that exact
revision. Expand the short architecture revision `182b628` to its full commit
and verify that the pinned training code matches it. Then download by passing
the full 40-character Hugging Face commit:

```bash
pretraining/lrs3-lipreader-visual-only/download.sh <commit-sha>
```

The script writes to:

```text
pretraining/.cache/lrs3-lipreader-visual-only/<commit-sha>/
```

It also creates `SHA256SUMS` inside that ignored directory. After review, update
`source.json` with:

- the immutable revision;
- exact expected filenames, sizes, and SHA-256 values;
- the full Auto-AVSR architecture commit;
- any other tokenizer/config files in the Hub repository; and
- the result of the serialized-checkpoint safety review.

Only then should a separate change add an adapter or training initialization
path. The folder name `pretraining` is organizational and is not evidence that
this particular artifact is a pretraining checkpoint.

See the repository-wide [research roadmap](../RESEARCH_ROADMAP.md) for the
evaluation and promotion gates around this candidate.
