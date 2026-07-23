# External pretraining and model sources

This directory catalogs upstream checkpoints or training sources that may be
evaluated against Open-Altergo. It does not contain model weights.

Each source directory should contain:

- the upstream repository ID and type;
- an immutable 40-character commit revision;
- verified license and provenance notes;
- an explicit relationship to Open-Altergo;
- a downloader that writes only to the ignored `.cache/` directory; and
- SHA-256 checksums captured after a verified download.

An entry with `revision: null` or `license: unverified` is quarantined metadata.
It may be inspected and pinned, but it must not be loaded by training,
inference, CI, or a release.

Current sources:

- [`simonlesaumon/lrs3-lipreader-visual-only`](lrs3-lipreader-visual-only/README.md)
  — requested LRS3 visual-only candidate; revision, files, and license still
  require verification.

The supplied research set is triaged in
[`RESEARCH_ROADMAP.md`](RESEARCH_ROADMAP.md) and represented as structured
metadata in [`papers.json`](papers.json). Paper inclusion is not dependency,
license, or reproduction approval.

This directory is separate from `cloud/engine/src/model_manifest.json`, which
describes the currently active and pinned inference assets. Promoting a source
from here into the engine requires compatibility tests, provenance review,
license review, immutable hashes, and held-out evaluation.
