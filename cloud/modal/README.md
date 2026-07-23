# Modal provisioning

`app.py` builds the runtime image, mounts persistent Volumes, and invokes the
provider-independent commands in `training/`.

Install the local control-plane dependency:

```bash
pip install -r cloud/modal/requirements.txt
```

Run with credentials injected by Doppler:

```bash
doppler run -- modal run cloud/modal/app.py::prepare --dataset-name my-speaker
```

See [the complete guide](../../docs/modal-finetuning.md). No Modal or Doppler
credentials belong in this directory.
