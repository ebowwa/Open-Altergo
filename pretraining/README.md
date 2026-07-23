# External pretraining and model sources

This directory catalogs upstream checkpoints or training sources that may be
evaluated against Open-Altergo. It does not contain model weights.

Each source directory should contain:

- the upstream repository ID and type;
- an immutable 40-character commit revision;
- architecture, preprocessing, tokenizer, and training provenance;
- an explicit relationship to Open-Altergo;
- a downloader that writes only to the ignored `.cache/` directory; and
- SHA-256 checksums captured after a verified download.

An entry with `revision: null` cannot be reproduced yet. License metadata is
recorded but does not block local capability experiments. Redistribution and
commercial release decisions happen separately from model evaluation.

Current sources:

- [`simonlesaumon/lrs3-lipreader-visual-only`](lrs3-lipreader-visual-only/README.md)
  — primary English visual-only Auto-AVSR candidate, awaiting an immutable Hub
  revision and checksums before integration.
- [`VSRo-200`](vsro200/README.md) — Romanian sentence VSR, dataset metadata,
  and LRRo transfer heads; useful for supervision and robustness research, not
  an active English backend.

The supplied research set is triaged in
[`RESEARCH_ROADMAP.md`](RESEARCH_ROADMAP.md) and represented as structured
metadata in [`papers.json`](papers.json). Paper inclusion is not dependency,
or reproduction approval. The immediate implementation order is in
[`CAPABILITY_PLAN.md`](CAPABILITY_PLAN.md).

This directory is separate from `cloud/engine/src/model_manifest.json`, which
describes the currently active and pinned inference assets. Promoting a source
from here into the engine requires compatibility tests, immutable hashes, and
held-out evaluation. Distribution policy is evaluated when packaging or
shipping the resulting backend.
