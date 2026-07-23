"""Pinned, checksum-verified model asset downloads."""

import argparse
import hashlib
import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path


MANIFEST_FILENAME = "model_manifest.json"


class ModelIntegrityError(RuntimeError):
    """A model asset did not match its pinned manifest entry."""


@lru_cache(maxsize=1)
def load_model_manifest():
    resource = files("open_altergo_engine").joinpath(MANIFEST_FILENAME)
    return json.loads(resource.read_text(encoding="utf-8"))


def model_file_spec(filename):
    manifest = load_model_manifest()
    try:
        return manifest["files"][filename]
    except KeyError as error:
        expected = ", ".join(sorted(manifest["files"]))
        raise ValueError(
            f"Unknown model file {filename!r}; expected one of: {expected}"
        ) from error


def sha256_file(path, chunk_size=8 * 1024 * 1024):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_checksum(path, *, expected_sha256, expected_size=None, label=None):
    path = Path(path)
    name = label or path.name
    if not path.is_file():
        raise ModelIntegrityError(f"Model asset is missing: {path}")

    actual_size = path.stat().st_size
    if expected_size is not None and actual_size != expected_size:
        raise ModelIntegrityError(
            f"{name} has size {actual_size}, expected {expected_size}"
        )

    actual_sha256 = sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise ModelIntegrityError(
            f"{name} failed SHA-256 verification: "
            f"got {actual_sha256}, expected {expected_sha256}"
        )
    return path


def verify_model_file(path, filename=None):
    filename = filename or Path(path).name
    spec = model_file_spec(filename)
    return verify_checksum(
        path,
        expected_sha256=spec["sha256"],
        expected_size=spec["size"],
        label=filename,
    )


def download_model_file(
    filename,
    *,
    cache_dir=None,
    local_dir=None,
    force_download=False,
    downloader=None,
):
    """Download a pinned file and verify it before returning its path.

    A corrupt cached file is force-downloaded once. The second failed
    verification is terminal.
    """

    model_file_spec(filename)
    manifest = load_model_manifest()
    if downloader is None:
        from huggingface_hub import hf_hub_download

        downloader = hf_hub_download

    arguments = {
        "repo_id": manifest["repository_id"],
        "revision": manifest["revision"],
        "filename": filename,
        "force_download": force_download,
    }
    if cache_dir:
        arguments["cache_dir"] = str(cache_dir)
    if local_dir:
        arguments["local_dir"] = str(local_dir)

    path = Path(downloader(**arguments))
    try:
        return str(verify_model_file(path, filename))
    except ModelIntegrityError:
        if force_download:
            raise
        arguments["force_download"] = True
        path = Path(downloader(**arguments))
        return str(verify_model_file(path, filename))


def download_model_bundle(*, cache_dir=None, local_dir=None, force_download=False):
    manifest = load_model_manifest()
    return {
        filename: download_model_file(
            filename,
            cache_dir=cache_dir,
            local_dir=local_dir,
            force_download=force_download,
        )
        for filename in manifest["files"]
    }


def _build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show", help="print the pinned manifest")
    show.set_defaults(handler=lambda args: print(json.dumps(load_model_manifest(), indent=2)))

    download = subparsers.add_parser(
        "download",
        help="download and verify the complete model bundle",
    )
    download.add_argument("--cache-dir")
    download.add_argument("--local-dir")
    download.add_argument("--force", action="store_true")

    verify = subparsers.add_parser("verify", help="verify one downloaded file")
    verify.add_argument("path")
    verify.add_argument(
        "--filename",
        help="manifest filename when the local file was renamed",
    )
    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "show":
        args.handler(args)
        return 0
    if args.command == "download":
        downloaded = download_model_bundle(
            cache_dir=args.cache_dir,
            local_dir=args.local_dir,
            force_download=args.force,
        )
        for filename, path in downloaded.items():
            print(f"{filename}: {path}")
        return 0
    verified = verify_model_file(args.path, args.filename)
    print(f"verified: {verified}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
