# Apple clients

This directory is the home of native Open-Altergo clients. The first shipping
target is iOS. A macOS client should follow after the iOS networking, models,
and product behavior are stable.

The first release is a thin SwiftUI client:

```text
iPhone capture or video import
        │
        └── HTTPS ──► HTTP API ──► Python API ──► inference engine
```

It does not embed Python, Gradio, or the model. On-device inference is a later,
separately planned distribution.

## Start here on a Mac

Do not improvise the project structure from this README. The implementation
documents are the executable specification:

1. [CLAUDE.md](CLAUDE.md) — rules for an autonomous coding agent.
2. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — product scope and native
   architecture.
3. [API.md](API.md) — the exact server contract and planned personalization
   boundary.
4. [TESTING.md](TESTING.md) — test matrix and required evidence.
5. [RELEASE.md](RELEASE.md) — CI, signing, App Store Connect, and TestFlight.
6. [TASKS.md](TASKS.md) — the ordered implementation queue and acceptance
   criteria.
7. [CLAUDE_LOOP.md](CLAUDE_LOOP.md) — a ready-to-paste Claude Code prompt.
8. [PATTERNS.md](PATTERNS.md) — which existing repository conventions this plan
   adopts and which hazards it deliberately avoids.

On the Mac, the automated entry point is:

```bash
apps/apple/scripts/claude-loop.sh
```

It runs Claude Code through the `seed` / `prd` Doppler scope, matching the
repository owner's normal local invocation.

No Xcode project has been generated yet. Generate it on macOS with the Xcode
version that will actually compile and test it; do not commit a guessed project
created or edited on another platform.

## Product boundary

The iOS MVP will:

- record visual-only video with the front camera or import a video;
- review the clip before upload;
- submit it to `POST /v1/transcriptions`;
- show the transcript, timed segments, and alternate hypotheses;
- support copy, share, correction, retry, cancellation, and useful errors;
- retain history only when the user chooses to do so;
- expose server health and privacy controls; and
- delete temporary recordings deterministically.

The MVP will not:

- bundle a model or run inference on the device;
- turn corrections or ordinary transcription clips into training data;
- promise background inference that the current synchronous API cannot
  support;
- record microphone audio; or
- ship personalization UI before the corresponding authenticated server
  contract exists.

## Privacy boundary

Recordings show a person's face and may reveal what they intended to say.
Treat recordings, expected text, transcripts, and personalized checkpoints as
sensitive user data.

Ordinary transcription and personalization are distinct consent paths.
Personalization collection must be explicit, revocable, user-scoped, and
deletable. A transcript correction is local product feedback unless the user
separately chooses to contribute it to personalization.

## Proposed directory shape

The first implementation task creates this flat, target-oriented layout:

```text
apps/apple/
├── project.yml
├── Config/
├── App/
├── Features/
│   ├── Capture/
│   ├── Transcription/
│   ├── History/
│   ├── Personalization/
│   └── Settings/
├── Core/
│   ├── API/
│   ├── Capture/
│   ├── Diagnostics/
│   ├── Persistence/
│   └── Security/
├── Shared/
├── Tests/
├── UITests/
├── Fixtures/
├── scripts/
└── fastlane/screenshots/en-US/
```

There is no redundant `src/OpenAltergo` wrapper and no local Swift package at
the start. Add a package only when code genuinely needs to be consumed by more
than one independently built Apple product.
