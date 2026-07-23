# LRS3 lipreader visual-only candidate

Upstream:
[`simonlesaumon/lrs3-lipreader-visual-only`](https://huggingface.co/simonlesaumon/lrs3-lipreader-visual-only)

This entry records the requested Hugging Face repository without committing its
weights or pretending that unverified metadata is known.

## Current status

| Field | Status |
| --- | --- |
| Repository type | Assumed model repository; verify against Hub metadata |
| Immutable revision | Unresolved |
| File inventory | Unverified |
| Architecture/config | Unverified |
| License | Unverified |
| LRS3 provenance and use restrictions | Unverified |
| Open-Altergo compatibility | Not tested |
| Active in training or inference | No |

The repository was not reachable from the environment that created this entry,
and no indexed model card was available. Do not infer the license from the
repository name or from unrelated LRS3 checkpoints.

## Pin and download on a connected machine

Resolve the upstream `main` commit:

```bash
git ls-remote \
  https://huggingface.co/simonlesaumon/lrs3-lipreader-visual-only \
  refs/heads/main
```

Review the model card, file tree, file sizes, Git/Xet history, and license at
that exact revision. Then download it by passing the full 40-character commit:

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
- the actual declared license;
- original authors and upstream training provenance; and
- whether the checkpoint is pretrained, fine-tuned, or only exported for
  inference.

Only then should a separate change add an adapter or training initialization
path. The folder name `pretraining` is organizational and is not evidence that
this particular artifact is a pretraining checkpoint.

See the repository-wide [research roadmap](../RESEARCH_ROADMAP.md) for the
evaluation and promotion gates around this candidate.
