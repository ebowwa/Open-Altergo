import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from open_altergo_engine import model_assets


class ModelManifestTests(unittest.TestCase):
    def test_manifest_is_pinned_and_complete(self):
        manifest = model_assets.load_model_manifest()

        self.assertEqual(
            manifest["repository_id"],
            "aaahmet/silent-lip-reader-model",
        )
        self.assertEqual(
            manifest["revision"],
            "ff1e35515594eb4562c469b99d147cf6a3d2891e",
        )
        self.assertEqual(
            set(manifest["files"]),
            {
                "pytorch_model.pt",
                "unigram5000.model",
                "unigram5000_units.txt",
            },
        )

    def test_checksum_verification_accepts_exact_file(self):
        content = b"verified model asset"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "asset.bin"
            path.write_bytes(content)

            verified = model_assets.verify_checksum(
                path,
                expected_sha256=hashlib.sha256(content).hexdigest(),
                expected_size=len(content),
            )

        self.assertEqual(verified.name, "asset.bin")

    def test_checksum_verification_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "asset.bin"
            path.write_bytes(b"corrupt")

            with self.assertRaises(model_assets.ModelIntegrityError):
                model_assets.verify_checksum(
                    path,
                    expected_sha256="0" * 64,
                    expected_size=7,
                )

    def test_download_uses_pinned_revision_and_retries_corrupt_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unigram5000.model"
            path.write_bytes(b"placeholder")
            calls = []

            def downloader(**kwargs):
                calls.append(kwargs)
                return str(path)

            with patch.object(
                model_assets,
                "verify_model_file",
                side_effect=[
                    model_assets.ModelIntegrityError("corrupt"),
                    path,
                ],
            ):
                result = model_assets.download_model_file(
                    "unigram5000.model",
                    downloader=downloader,
                )

        self.assertEqual(result, str(path))
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            calls[0]["revision"],
            "ff1e35515594eb4562c469b99d147cf6a3d2891e",
        )
        self.assertFalse(calls[0]["force_download"])
        self.assertTrue(calls[1]["force_download"])


if __name__ == "__main__":
    unittest.main()
