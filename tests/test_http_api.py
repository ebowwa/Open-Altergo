import unittest

from fastapi.testclient import TestClient

from apis.http_api.app import create_app


class FakeService:
    def __init__(self):
        self.is_loaded = False
        self.calls = []
        self.path_exists_during_call = False
        self.last_path = None

    def transcribe(self, path, **kwargs):
        self.last_path = path
        self.path_exists_during_call = path.is_file()
        self.calls.append((path, kwargs))
        return {
            "transcript": "hello world",
            "segments": [],
            "n_segments": 0,
        }


class HttpApiTests(unittest.TestCase):
    def setUp(self):
        self.service = FakeService()
        self.client = TestClient(create_app(self.service))

    def test_health_does_not_load_model(self):
        response = self.client.get("/health")

        self.assertEqual(
            response.json(),
            {"status": "ok", "model_loaded": False},
        )

    def test_transcription_forwards_options_and_removes_upload(self):
        response = self.client.post(
            "/v1/transcriptions",
            files={"video": ("clip.mp4", b"video-bytes", "video/mp4")},
            data={"hflip": "true", "nbest": "3", "max_seconds": "12"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["transcript"], "hello world")
        self.assertTrue(self.service.path_exists_during_call)
        self.assertEqual(
            self.service.calls[0][1],
            {"nbest": 3, "hflip": True, "max_seconds": 12},
        )
        self.assertFalse(self.service.last_path.exists())

    def test_empty_upload_is_rejected(self):
        response = self.client.post(
            "/v1/transcriptions",
            files={"video": ("clip.mp4", b"", "video/mp4")},
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_decode_options_are_rejected_before_inference(self):
        response = self.client.post(
            "/v1/transcriptions",
            files={"video": ("clip.mp4", b"video", "video/mp4")},
            data={"nbest": "0"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.service.calls, [])


if __name__ == "__main__":
    unittest.main()
