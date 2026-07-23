import unittest

from python_api.core import RuntimeConfig, SilentSpeechService
from python_api.core.service import _find_project_root


class FakeReader:
    def __init__(self):
        self.calls = []

    def transcribe(self, path, nbest=5, hflip=False, max_seconds=40):
        self.calls.append(("transcribe", path, nbest, hflip, max_seconds))
        return {"segments": [], "transcript": "", "n_segments": 0}

    def transcribe_auto(self, path, nbest=5, max_seconds=40):
        self.calls.append(("transcribe_auto", path, nbest, max_seconds))
        return {"segments": [], "transcript": "", "n_segments": 0}


class RuntimeConfigTests(unittest.TestCase):
    def test_reads_environment_without_ui_dependency(self):
        config = RuntimeConfig.from_env(
            {
                "LIPREAD_DEVICE": "mps",
                "LIPREAD_DETECTOR": "retinaface",
                "LIPREAD_CKPT": "/models/personal.pt",
            }
        )

        self.assertEqual(config.device, "mps")
        self.assertEqual(config.detector, "retinaface")
        self.assertEqual(config.checkpoint_path, "/models/personal.pt")

    def test_empty_checkpoint_is_normalized_to_none(self):
        self.assertIsNone(RuntimeConfig.from_env({"LIPREAD_CKPT": ""}).checkpoint_path)

    def test_checkout_engine_package_is_discoverable(self):
        root = _find_project_root()

        self.assertTrue(
            (
                root
                / "cloud"
                / "engine"
                / "src"
                / "pipeline.py"
            ).is_file()
        )


class SilentSpeechServiceTests(unittest.TestCase):
    def setUp(self):
        self.reader = FakeReader()
        self.factory_calls = []

        def factory(config):
            self.factory_calls.append(config)
            return self.reader

        self.config = RuntimeConfig(device="cpu", detector="mediapipe")
        self.service = SilentSpeechService(self.config, reader_factory=factory)

    def test_model_is_loaded_lazily_and_only_once(self):
        self.assertFalse(self.service.is_loaded)

        self.service.transcribe("first.mp4")
        self.service.transcribe("second.mp4")

        self.assertTrue(self.service.is_loaded)
        self.assertEqual(self.factory_calls, [self.config])

    def test_transcribe_forwards_interface_options(self):
        result = self.service.transcribe(
            "clip.mp4",
            nbest=3,
            hflip=True,
            max_seconds=12,
        )

        self.assertEqual(result["transcript"], "")
        self.assertEqual(
            self.reader.calls,
            [("transcribe", "clip.mp4", 3, True, 12)],
        )

    def test_transcribe_auto_uses_backend_auto_orientation(self):
        self.service.transcribe_auto("clip.mp4", nbest=2, max_seconds=9)

        self.assertEqual(
            self.reader.calls,
            [("transcribe_auto", "clip.mp4", 2, 9)],
        )

    def test_missing_video_is_rejected_before_model_load(self):
        with self.assertRaisesRegex(ValueError, "video_path is required"):
            self.service.transcribe("")

        self.assertFalse(self.service.is_loaded)


if __name__ == "__main__":
    unittest.main()
