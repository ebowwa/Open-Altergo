# Model assets, integrity, and provenance

Open-Altergo does not commit model weights or tokenizer binaries to GitHub.
Runtime assets are downloaded from:

```text
repository: aaahmet/silent-lip-reader-model
revision:   ff1e35515594eb4562c469b99d147cf6a3d2891e
license:    MIT
```

The immutable revision and hashes are stored in the packaged
`open_altergo_engine/model_manifest.json`.

| File | Bytes | SHA-256 |
|---|---:|---|
| `pytorch_model.pt` | 1,001,892,616 | `fbf7cd70ff1c0e694b3030fb779dbb4570f04e4b841d62f9296c229e94878ddb` |
| `unigram5000.model` | 327,113 | `2c1d648ccf5fdce6612ecbea2ffbd1cab5aabc90458781186175c3911c4bdb1e` |
| `unigram5000_units.txt` | 73,778 | `29001d967ad290e28f6f1d7d47e07e314354bf67d3b1f494e936fa2fed9a9122` |

## Download

Install the engine, then download and verify every file:

```bash
pip install -e cloud/engine
python -m open_altergo_engine.model_assets download \
  --local-dir ./models/silent-lip-reader
```

Inspect the effective manifest:

```bash
python -m open_altergo_engine.model_assets show
```

Verify a previously downloaded file:

```bash
python -m open_altergo_engine.model_assets verify \
  ./models/silent-lip-reader/pytorch_model.pt
```

Runtime downloads use the same manifest. A corrupt cache entry is downloaded
once more and rechecked; a second mismatch stops execution before model
loading.

## Provenance

- Architecture and original training work: Auto-AVSR, Pingchuan Ma et al.
- Checkpoint source identified by the mirror: `AD1TEYA/lip-reading-model`.
- Mirror and surrounding Silent Lip Reader demo: Ahmet Dedeler (`aaahmet`).
- Mirror: <https://huggingface.co/aaahmet/silent-lip-reader-model>

The checkpoint is a PyTorch pickle/state dictionary. Open-Altergo verifies its
pinned SHA-256 checksum before loading and requests PyTorch's
`weights_only=True` mode. Custom personalized checkpoints supplied through
`LIPREAD_CKPT` are user-controlled and are not expected to match the base-model
manifest.
