# iOS implementation plan

## 1. Goal

Ship a private-by-default iPhone client that captures or imports a short video,
sends it to the Open-Altergo HTTP service, and makes the resulting silent-speech
transcript useful. The implementation must be understandable to a coding agent,
testable without model inference, and ready for a controlled TestFlight path.

Success for the first internal TestFlight build means:

- a new user can understand what leaves the device;
- the app records video without requesting microphone access;
- import and capture both produce a reviewable clip;
- a healthy configured server can return a transcript;
- no-face, timeout, offline, server, invalid-response, and cancellation paths
  are usable;
- temporary clips are removed according to the user's retention choice;
- unit, contract, and UI tests pass in CI;
- the physical-device checklist has evidence; and
- App Store Connect shows the exact uploaded build as processed.

Model quality is not an iOS acceptance criterion. It is measured separately
against held-out data.

## 2. Decisions fixed for MVP

| Area | Decision |
| --- | --- |
| UI | Native SwiftUI |
| Language | Swift 6 with strict concurrency |
| Minimum OS | iOS 17 |
| Project definition | XcodeGen `project.yml`; generated project is disposable |
| Runtime dependencies | Apple frameworks only initially |
| Persistence | SwiftData metadata plus protected files in Application Support |
| Capture | AVFoundation front-camera, video-only |
| Import | `PhotosPicker` video transfer |
| Networking | `URLSession`, streamed multipart upload |
| Current inference | Remote HTTP API |
| Secrets | Keychain on device; Doppler on the trusted release runner |
| PR CI | GitHub-hosted macOS, unsigned and secret-free |
| TestFlight CI | Trusted self-hosted Apple Silicon runner |
| Release signal | reviewed `main` commit advanced to `bump`, or explicit dispatch |
| Personalization | disabled until separate authenticated APIs exist |

Use the latest stable Xcode available on the development Mac. CI records and
pins its exact `DEVELOPER_DIR`; changing Xcode is an intentional build change.

## 3. User journeys

### 3.1 First launch

1. Explain that the app transcribes visible speech from video.
2. Explain that the MVP uploads the chosen clip to the configured service.
3. State that microphone audio is not captured.
4. Let the user continue without asking for camera or photo permissions.
5. Ask for camera access only after they tap Record. `PhotosPicker` should use
   the system selection flow rather than broad library access.

### 3.2 Capture and transcribe

1. Home presents Record and Import.
2. Record opens a front-camera preview and clear framing guidance.
3. User starts and stops a clip; enforce the configured duration limit.
4. Review shows playback, duration, retake/delete, mirror setting, and Submit.
5. Submit shows preparation, upload progress, server processing, and Cancel.
6. Result shows the full transcript, timed segments, and alternatives.
7. User may copy, share, correct locally, retry, or delete.
8. History is retained only under the selected retention policy.

### 3.3 Failure recovery

- Camera denied: explain and offer a Settings deep link plus Import.
- No face: retain the review clip long enough to retry and show framing advice.
- Offline: do not silently queue an ordinary transcription; offer Retry.
- Timeout/server unavailable: preserve user intent and show a retryable error.
- Invalid response: log a redacted diagnostic identifier, never transcript data.
- Cancel: cancel URLSession work, remove multipart temporary files, and return
  to a deterministic state.
- Relaunch after interruption: purge orphaned temporary files older than the
  documented grace period.

### 3.4 Personalization, later

Personalization is not a hidden extension of transcription. Its future journey:

1. User reads a separate consent and retention explanation.
2. Server creates a user-scoped collection session.
3. App presents a server-versioned prompt.
4. App records the prompt and allows review.
5. User explicitly uploads the video paired with exact prompt ID and text.
6. App displays collection completeness, deletion, and training-job status.
7. Server splits data by recording session, evaluates a held-out set, and
   exposes model activation only after metrics are available.
8. User can revoke consent, delete examples, delete a model, and export a
   manifest of their data.

## 4. Interface map

```text
Onboarding
    └── Home
        ├── Capture ──► Review ──► Upload/Processing ──► Result
        ├── Import  ──► Review ──► Upload/Processing ──► Result
        ├── History ───────────────────────────────────► Result
        └── Settings
            ├── Server and health
            ├── Retention and delete-all
            ├── Diagnostics
            └── Personalization (feature-gated)
```

Every primary control receives a stable accessibility identifier before UI
tests are written.

## 5. Source layout and ownership

```text
App/
├── OpenAltergoApp.swift
├── AppEnvironment.swift
├── AppRouter.swift
└── RootView.swift
Features/
├── Onboarding/
├── Capture/
├── Transcription/
├── History/
├── Personalization/
└── Settings/
Core/
├── API/
│   ├── TranscriptionClient.swift
│   ├── URLSessionTranscriptionClient.swift
│   ├── MultipartBody.swift
│   ├── APIModels.swift
│   └── APIError.swift
├── Capture/
│   ├── VideoCaptureService.swift
│   ├── AVVideoCaptureService.swift
│   └── ImportedVideoStore.swift
├── Persistence/
│   ├── HistoryStore.swift
│   ├── SwiftDataHistoryStore.swift
│   └── TemporaryMediaStore.swift
├── Security/
│   ├── CredentialStore.swift
│   └── KeychainCredentialStore.swift
└── Diagnostics/
    ├── DiagnosticsClient.swift
    └── RedactedLogger.swift
Shared/
├── Components/
├── Formatting/
└── Accessibility/
```

Feature folders own presentation state, views, and navigation for that feature.
Core folders own platform and server boundaries. Shared contains only genuinely
reused UI or formatting. Avoid a generic `Utils` folder.

The future macOS target can compile selected `Core` and `Shared` files. Extract
a Swift package only when that second target proves a stable package boundary.

## 6. State and concurrency

Use explicit state machines rather than scattered booleans.

Capture:

```text
idle
 └─► requestingPermission
      ├─► previewing ─► recording ─► reviewing
      └─► denied
any ─► failed
```

Transcription:

```text
idle ─► preparing ─► uploading(progress) ─► processing
                                      ├────► completed
                                      ├────► failed(retryability)
                                      └────► cancelled
```

Personalization upload:

```text
localOnly ─► queued ─► uploading ─► uploaded
                         ├────────► failed
                         └────────► deleted
```

Use one `@MainActor` observable model per screen or bounded flow. Make the
concrete network client, media store, and persistence store actors where they
own mutable state. Send immutable value types across isolation boundaries.

Required protocols:

```swift
protocol TranscriptionClient: Sendable {
    func health() async throws -> HealthResponse
    func transcribe(_ request: TranscriptionRequest) async throws
        -> AsyncThrowingStream<TranscriptionEvent, Error>
}

protocol VideoCaptureService: Sendable { /* permission, preview, start, stop */ }
protocol HistoryStore: Sendable { /* list, save, update, delete, deleteAll */ }
protocol CredentialStore: Sendable { /* read, save, delete */ }
```

The event stream can represent upload progress and completion without exposing
`URLSessionTask` to a view.

## 7. Capture and media lifecycle

- Configure `AVCaptureSession` off the main thread.
- Add only the front camera input and movie/video output. Never add audio input.
- Preserve orientation metadata and record whether the preview was mirrored.
- Default the request's `hflip` based on the actual saved-file orientation,
  not merely the mirrored preview. Let the review screen override it.
- Enforce 40 seconds in UI for the first release even though the server accepts
  up to 120; make this a configuration value covered by tests.
- Prefer a server-compatible `.mov` or `.mp4` without wasteful transcoding.
- Inspect duration and readable file size before submission.
- Keep active capture and multipart files in a protected temporary directory.
- Move a clip into protected Application Support only when the retention choice
  requires it.
- Apply complete file protection where usable and document any background
  transfer trade-off before changing protection class.
- On launch, remove abandoned temporary media older than 24 hours.

## 8. Networking

The current request is synchronous from the server's perspective. Use a
foreground `URLSession` for MVP:

- create multipart content on disk or as a bounded stream;
- report upload progress through a delegate;
- map HTTP and decoding failures into typed `APIError`;
- enforce client timeouts longer than the server's expected inference window;
- support task cancellation;
- accept a redacted server request ID if the API later returns one; and
- never retry a non-idempotent upload automatically without user intent.

A background session is reserved for future resumable personalization uploads.
It does not make a synchronous inference request reliable while suspended.

Release configuration must have an HTTPS base URL. A Debug-only local
configuration may use the Mac's LAN URL with a narrowly scoped transport
exception. Never add a global arbitrary-load exception.

The current API has no authentication contract. Do not invent a header in the
client. Before public distribution, add user-scoped server authentication,
store its token in Keychain, and contract-test it.

## 9. Local data

Use SwiftData for lightweight history metadata:

- local ID;
- creation date;
- source (`capture` or `import`);
- duration;
- transcript;
- segments and alternatives as versioned encoded data;
- optional retained-media relative path;
- correction, kept locally by default;
- server request ID when available; and
- schema version.

Never persist bearer tokens, multipart bodies, or raw HTTP logs in SwiftData.
Persisted file paths are relative to the app-controlled root, not absolute.

Settings:

- onboarding completion;
- retention mode: `deleteAfterResult` by default, optional `keepHistory`;
- development server URL only in Debug;
- requested alternatives and duration cap; and
- feature flags supplied by build configuration.

Provide delete-one, delete-all, and export-transcript behavior. If a retained
file deletion fails, keep a tombstone and retry; do not pretend the data is gone.

## 10. Configuration

`project.yml` will define:

- `OpenAltergo` application target;
- `OpenAltergoTests`;
- `OpenAltergoUITests`;
- Debug, Release, and UITesting configurations;
- generated Info.plist values;
- camera usage description;
- no microphone usage description;
- code-signing settings supplied outside source control; and
- a Release base URL supplied by an `.xcconfig` or build setting.

Checked-in configuration contains no team ID, App Store app ID, key ID,
certificate, profile, token, private endpoint, or developer home path.

Use repository/environment variables for non-secret CI identifiers and Doppler
for secrets. A generated `Local.xcconfig` may contain developer-specific values
and must be ignored.

## 11. Observability

Use `Logger` categories for lifecycle, capture, networking, persistence, and
release diagnostics. Log:

- redacted request identifier;
- state transition;
- HTTP status;
- byte count;
- duration; and
- typed failure category.

Do not log:

- transcript or correction text;
- video filenames supplied by a user;
- prompt text;
- tokens or headers;
- full server responses; or
- filesystem paths containing user names.

The Settings diagnostics screen shows app version/build, OS, API base host
without path or credentials, health status, and recent redacted error codes.

## 12. Accessibility and presentation

- Dynamic Type through accessibility sizes.
- VoiceOver labels and values for controls, progress, transcript segments, and
  recording state.
- Do not communicate upload or recording state by color alone.
- Respect Reduce Motion.
- Minimum hit targets and sufficient contrast.
- Captions/instructions must not imply audio is being captured.
- UI tests cover the largest supported content-size category on one flow.

## 13. Later macOS target

After iOS internal TestFlight:

- reuse API DTOs, client, history schema, redacted logging, and result UI where
  appropriate;
- create macOS-specific capture permissions, camera session, windows, menus,
  and keyboard commands;
- decide Mac App Store versus Developer ID distribution as a product choice;
- keep those signing/notarization paths separate; and
- do not block iOS MVP on Core ML export or native face alignment.

## 14. Definition of done

A task is done only when:

- implementation and public API names match these documents or the decision log
  explains the change;
- relevant tests pass;
- generated project consistency is checked;
- logs and artifacts contain no sensitive content;
- accessibility identifiers exist for changed interactive UI;
- visual work has inspected screenshot evidence;
- physical-only claims have physical evidence; and
- `TASKS.md` records the exact command and result.
