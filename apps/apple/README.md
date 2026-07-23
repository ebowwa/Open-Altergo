# Apple clients

This directory is reserved for native macOS and iOS clients. The first versions
should be thin Swift applications that capture video, submit it to the
Open-Altergo HTTP API, and present the returned transcript. They consume the
hosted Python inference system; they do not bundle Gradio or embed the Python
engine.

```text
iOS / macOS capture and UI
        │
        └── HTTPS ──► HTTP API ──► Python API ──► engine
```

## Initial product boundary

- Record or select a video and request visual-only transcription.
- Display transcript, alternatives, timing, and useful failure states.
- Keep server URL and authentication configuration outside the source tree.
- Treat local recordings and transcripts as private user data.
- Support explicit deletion of any locally retained recording or transcript.

The iOS and macOS targets may share Swift networking and data models while
using platform-specific capture, permissions, lifecycle, and interface code.
No Apple project has been generated yet.

## Personalization and refinement

Apple clients can later help users build a personalized lip-reading model by
recording prompted sentences and, when the user explicitly opts in, uploading
the video with its exact prompt text and session metadata. That is a separate
workflow from ordinary transcription.

Collection must be:

- explicit and revocable, never enabled by default;
- labeled with the expected transcript rather than inferred as ground truth;
- split by recording session for honest train, validation, and test evaluation;
- encrypted in transit and protected by authenticated, user-scoped storage;
- accompanied by retention, export, and deletion controls;
- excluded from general model training unless separately authorized.

The current HTTP API does not expose dataset collection or training endpoints.
Those contracts should be designed separately so a transcription request
cannot silently become training data.

## Later on-device option

On-device inference is a different distribution. It requires exporting the
visual frontend, Conformer, and decoder to an Apple-supported runtime and
reimplementing face alignment and video preprocessing in native code. It should
not be treated as a prerequisite for the first macOS or iOS clients.
