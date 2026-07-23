import os
import unittest

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr

from silent_speech.interfaces import gradio_app


def tearDownModule():
    gradio_app.demo.close()


class FakeService:
    def __init__(self, output=None, error=None):
        self.output = output
        self.error = error
        self.calls = []

    def transcribe(self, video, **kwargs):
        self.calls.append((video, kwargs))
        if self.error:
            raise self.error
        return self.output


class GradioHandlerTests(unittest.TestCase):
    def test_formats_transcript_and_segment_breakdown(self):
        service = FakeService(
            {
                "transcript": "hello world",
                "segments": [
                    {"text": "hello", "seg_time": [0.0, 1.2]},
                    {"text": "world", "seg_time": [1.2, 2.5]},
                ],
            }
        )

        transcript, breakdown = gradio_app.create_handler(service)(
            "clip.mp4",
            True,
        )

        self.assertEqual(transcript, "hello world")
        self.assertIn("[ 0.0– 1.2s]  hello", breakdown)
        self.assertIn("[ 1.2– 2.5s]  world", breakdown)
        self.assertEqual(
            service.calls,
            [("clip.mp4", {"nbest": 5, "hflip": True})],
        )

    def test_missing_video_does_not_call_core(self):
        service = FakeService({})

        result = gradio_app.create_handler(service)(None, False)

        self.assertEqual(
            result,
            ("Please record or upload a video first.", ""),
        )
        self.assertEqual(service.calls, [])

    def test_no_segments_returns_actionable_message(self):
        service = FakeService({"transcript": "", "segments": []})

        transcript, breakdown = gradio_app.create_handler(service)(
            "clip.mp4",
            False,
        )

        self.assertIn("No face / no speech detected", transcript)
        self.assertEqual(breakdown, "")

    def test_backend_exception_is_reported_without_crashing_ui(self):
        service = FakeService(error=RuntimeError("backend failed"))

        transcript, breakdown = gradio_app.create_handler(service)(
            "clip.mp4",
            False,
        )

        self.assertIn("RuntimeError: backend failed", transcript)
        self.assertEqual(breakdown, "")

    def test_default_model_remains_lazy_after_ui_import(self):
        self.assertIsInstance(gradio_app.demo, gr.Blocks)
        self.assertFalse(gradio_app.default_service.is_loaded)


class CompatibilityLauncherTests(unittest.TestCase):
    def test_root_app_exports_packaged_interface(self):
        import app

        self.assertIs(app.demo, gradio_app.demo)
        self.assertIs(app.run, gradio_app.run)


if __name__ == "__main__":
    unittest.main()
