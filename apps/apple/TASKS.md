# iOS execution queue

Complete tasks in dependency order. A checked box requires its acceptance
criteria and Evidence line to be filled with real results. Use `BLOCKED:` with
the exact human action when a gate cannot be completed.

## Phase 0 — Mac and product bootstrap

- [ ] **IOS-001 — Mac doctor and repository-local build paths**
  - Dependencies: none.
  - Create `scripts/doctor.sh` and `.gitignore` entries for `.build`,
    `Local.xcconfig`, generated secrets, archives, and exports.
  - Check Xcode, command-line tools, Swift, XcodeGen, available simulators, Git
    cleanliness, and required repository paths.
  - Never mutate global developer state.
  - Acceptance: succeeds on the target Mac; an intentionally missing tool gives
    an actionable nonzero failure.
  - Evidence: `TBD`

- [ ] **IOS-002 — Confirm Apple identity and release configuration**
  - Dependencies: IOS-001.
  - Human gate: confirm app name, final bundle ID, Apple team, App Store Connect
    record, intended production API host, and internal tester group.
  - Put values in protected repository/environment variables, not source.
  - Acceptance: exact bundle ID exists in both Developer portal and ASC; IDs are
    recorded without secrets; Release HTTPS host is known.
  - Evidence: `TBD (record identifiers by variable name, not secret value)`

- [ ] **IOS-003 — Generate the minimal XcodeGen project**
  - Dependencies: IOS-001; IOS-002 may remain blocked if Debug uses a safe local
    identifier, but Release archive cannot proceed.
  - Add pinned XcodeGen setup, `project.yml`, Config xcconfigs, app target, unit
    test target, UI test target, and scheme.
  - Use a flat `apps/apple` source layout and repo-local DerivedData.
  - Acceptance: generation is deterministic; app launches to a static root
    screen; unsigned simulator build and empty test targets pass.
  - Evidence: `TBD`

## Phase 1 — Application foundation

- [ ] **IOS-010 — Dependency injection and app routing**
  - Dependencies: IOS-003.
  - Add `AppEnvironment`, root navigation, feature boundaries, preview/test
    dependencies, and no global business-state singleton.
  - Acceptance: unit test proves production and mock environments construct;
    app compiles under Swift 6 strict concurrency.
  - Evidence: `TBD`

- [ ] **IOS-011 — Design tokens and accessibility contract**
  - Dependencies: IOS-010.
  - Add minimal color, type, spacing, button, card, error, progress, and empty
    state primitives using semantic system behavior.
  - Define stable accessibility identifier names.
  - Acceptance: light/dark and largest Dynamic Type screenshots inspected.
  - Evidence: `TBD`

- [ ] **IOS-012 — Onboarding and privacy choices**
  - Dependencies: IOS-010, IOS-011.
  - Explain remote processing, video-only capture, default deletion, and separate
    personalization consent. Do not request permissions on launch.
  - Acceptance: UI tests cover first launch, relaunch, and reset; copy never
    implies microphone capture or silent training-data collection.
  - Evidence: `TBD`

- [ ] **IOS-013 — Protected settings and credential stores**
  - Dependencies: IOS-010.
  - Add non-secret settings store, Keychain adapter, in-memory fakes, redacted
    errors, and configuration validation.
  - Acceptance: unit tests cover create/read/update/delete and fail-closed error
    behavior; no token appears in logs or preferences.
  - Evidence: `TBD`

## Phase 2 — HTTP contract

- [ ] **IOS-020 — Check in API fixtures and Swift DTOs**
  - Dependencies: IOS-003.
  - Add every fixture listed in `API.md`, explicit coding keys, validated range
    types, and additive-field tolerance.
  - Acceptance: Swift decoding tests and `python -m unittest
    tests.test_http_api` pass.
  - Evidence: `TBD`

- [ ] **IOS-021 — Streamed multipart encoder**
  - Dependencies: IOS-020.
  - Implement fixed-boundary test support, random production boundaries,
    scalar fields, file streaming/copy, content length, and deterministic
    cleanup.
  - Acceptance: byte-exact tiny fixture test; cancellation/failure cleanup test;
    memory does not scale by reading the complete clip into `Data`.
  - Evidence: `TBD`

- [ ] **IOS-022 — URLSession transcription client**
  - Dependencies: IOS-021, IOS-013.
  - Implement health, upload progress, completion, typed errors, cancellation,
    timeout, Debug base URL, and Release HTTPS enforcement.
  - Acceptance: deterministic URLProtocol/session tests cover success, no-face,
    400, 413, 422, 500, invalid JSON, timeout, offline, TLS rejection, and
    cancellation.
  - Evidence: `TBD`

- [ ] **IOS-023 — Server diagnostics UI**
  - Dependencies: IOS-022, IOS-011.
  - Show version/build, OS, redacted base host, health, model lazy-loaded state,
    and recent redacted failure categories.
  - Acceptance: health `model_loaded=false` is presented as healthy; no
    sensitive request or response content is rendered or logged.
  - Evidence: `TBD`

## Phase 3 — Video acquisition

- [ ] **IOS-030 — Temporary media lifecycle**
  - Dependencies: IOS-010.
  - Add protected directories, ownership model, atomic move, explicit delete,
    tombstones, and 24-hour orphan purge.
  - Acceptance: unit tests cover success, failure, cancellation, relaunch purge,
    and failed-delete retry.
  - Evidence: `TBD`

- [ ] **IOS-031 — PhotosPicker import**
  - Dependencies: IOS-030, IOS-011.
  - Import supported video to app-controlled temporary storage, inspect duration
    and size, and reject unreadable/over-limit media without broad Photos access.
  - Acceptance: deterministic tests and simulator UI flow cover local success,
    cancellation, unsupported media, and over-limit video; physical checklist
    owns iCloud-backed transfer.
  - Evidence: `TBD`

- [ ] **IOS-032 — Video-only front-camera service**
  - Dependencies: IOS-030.
  - Add permission state, front-camera preview, video output, start/stop,
    duration limit, orientation, mirroring metadata, and interruption handling.
  - Never add an audio input or microphone usage string.
  - Acceptance: service/state tests pass; project entitlement/Info inspection
    shows camera only; physical device evidence is still required.
  - Evidence: `TBD`

- [ ] **IOS-033 — Capture and review UI**
  - Dependencies: IOS-011, IOS-031, IOS-032.
  - Add framing guidance, record timer, stop, playback, retake, delete, mirror
    override, size/duration, and submit.
  - Acceptance: mock UI tests cover preview/record/review/retake and camera
    denied fallback; screenshots inspected.
  - Evidence: `TBD`

## Phase 4 — Transcription product

- [ ] **IOS-040 — Transcription state machine**
  - Dependencies: IOS-022, IOS-030.
  - Implement prepare/upload/process/complete/fail/cancel transitions with one
    owner for network and temporary media.
  - Acceptance: exhaustive transition tests reject invalid transitions and
    prove cleanup/retention for every terminal state.
  - Evidence: `TBD`

- [ ] **IOS-041 — Upload and processing UI**
  - Dependencies: IOS-033, IOS-040.
  - Show honest preparation/upload/processing phases, byte progress, cancel,
    and typed retry behavior.
  - Acceptance: UI tests cover progress, cancel, retryable server failure,
    nonretryable invalid clip, offline, and relaunch.
  - Evidence: `TBD`

- [ ] **IOS-042 — Transcript result**
  - Dependencies: IOS-041, IOS-020.
  - Show full transcript, timed segments, ranked alternatives, no-face guidance,
    copy, share, local correction, retry, and delete.
  - Never present beam score as a probability.
  - Acceptance: fixtures drive UI tests for all result forms; Dynamic Type,
    VoiceOver semantics, light/dark screenshots inspected.
  - Evidence: `TBD`

- [ ] **IOS-043 — Local history and retention**
  - Dependencies: IOS-030, IOS-042.
  - Add versioned SwiftData metadata, default delete-after-result, optional
    retained history/media, open, delete one, delete all, and transcript export.
  - Acceptance: migration/CRUD tests pass; failed file deletion remains visible
    as pending; UI tests prove the default does not retain video.
  - Evidence: `TBD`

## Phase 5 — Privacy, quality, and device validation

- [ ] **IOS-050 — Privacy manifest and logging audit**
  - Dependencies: IOS-043.
  - Add privacy manifest based on actual APIs, review Required Reason APIs,
    permission strings, file protection, logs, crash/test attachments, and local
    deletion.
  - Acceptance: no microphone usage; automated log-redaction tests pass;
    App Privacy worksheet is drafted from observed behavior.
  - Evidence: `TBD`

- [ ] **IOS-051 — Accessibility and localization readiness**
  - Dependencies: IOS-043.
  - Audit labels, focus order, Dynamic Type, contrast, Reduce Motion, hit areas,
    non-color state, and extract user-facing strings.
  - Acceptance: Accessibility Inspector/manual findings recorded; UI suite runs
    at large content size; screenshot evidence inspected.
  - Evidence: `TBD`

- [ ] **IOS-052 — Performance and leak baseline**
  - Dependencies: IOS-043.
  - Measure launch, capture readiness, multipart memory, repeated cycles,
    temporary storage, and thermal behavior.
  - Acceptance: target-device measurements recorded; no whole-file upload
    buffer or persistent temp-file growth; regression budgets proposed from
    evidence.
  - Evidence: `TBD`

- [ ] **IOS-053 — Physical iPhone 13 mini checklist**
  - Dependencies: IOS-050, IOS-051, IOS-052.
  - Execute every physical check in `TESTING.md`.
  - Acceptance: device/OS/build recorded, failures become tasks, microphone
    permission is absent, camera and mirroring are demonstrated.
  - Evidence: `TBD`

- [ ] **IOS-054 — Adam demo regression**
  - Dependencies: IOS-042.
  - Run the available Adam launch-demo video through the iOS client against the
    same server configuration used by the repository demo.
  - Do not commit the video unless its license explicitly permits redistribution.
  - Acceptance: record clip hash/provenance, server/model revision, request
    options, transcript response, app screenshot, and cleanup result. Describe
    observed output without inventing accuracy.
  - Evidence: `TBD or BLOCKED: demo file/provenance/server unavailable`

## Phase 6 — CI and TestFlight

- [ ] **IOS-060 — Secret-free hosted Apple CI**
  - Dependencies: IOS-020, IOS-040.
  - Add `apple-ci.yml` per `RELEASE.md`.
  - Acceptance: a public-style PR run builds/tests without secrets or
    self-hosted runner; artifacts appear on intentional failure.
  - Evidence: `TBD`

- [ ] **IOS-061 — Screenshot workflow**
  - Dependencies: IOS-042, IOS-060.
  - Add deterministic screenshot states, dimension checks, localization folder,
    and artifact workflow.
  - Acceptance: expected files exist, are visually inspected, and contain no
    real user data or private endpoint.
  - Evidence: `TBD`

- [ ] **IOS-062 — Trusted TestFlight workflow**
  - Dependencies: IOS-002, IOS-053, IOS-060.
  - Add release preflight, protected self-hosted workflow, existing keychain
    unlock, Doppler ASC key materialization, archive/export/upload, exact build
    polling, artifacts, and unconditional cleanup.
  - Acceptance: fork/PR cannot enter release job; ancestry and environment
    guards fail closed; dry run reaches pre-upload gate without secret leakage.
  - Evidence: `TBD`

- [ ] **IOS-063 — CI and ASC REST helper**
  - Dependencies: IOS-062.
  - Add dispatch, run-for-SHA, watch, and exact-build ASC commands without a
    mandatory `gh` or Fastlane dependency.
  - Acceptance: redacted tests/fixtures cover JWT claims, pagination, failures,
    and exact build selection; no token/key output.
  - Evidence: `TBD`

- [ ] **IOS-064 — App Store Connect metadata readiness**
  - Dependencies: IOS-002, IOS-050, IOS-061.
  - Finish app icon, screenshots, privacy policy/support URLs, App Privacy,
    export compliance, tester notes, and internal group.
  - Acceptance: readiness checklist reviewed against actual app behavior; no
    placeholder URL or inaccurate privacy answer remains.
  - Evidence: `TBD`

- [ ] **IOS-065 — First internal TestFlight**
  - Dependencies: IOS-053, IOS-062, IOS-063, IOS-064.
  - Advance `bump` to the reviewed `main` commit or use approved dispatch.
  - Acceptance: exact build processes in ASC, installs through TestFlight, and
    passes the TestFlight acceptance checks in `TESTING.md`.
  - Evidence: `TBD (build number, commit SHA, processed state, tester/device)`

## Phase 7 — Personalization after server support

- [ ] **IOS-070 — Approve personalization contract**
  - Dependencies: IOS-065.
  - Implement and test the proposed authenticated server endpoints in `API.md`,
    retention policy, export/delete, session-level splitting, and job status.
  - Acceptance: Python contract tests and privacy threat review pass.
  - Evidence: `TBD`

- [ ] **IOS-071 — Feature-gated consent and prompt flow**
  - Dependencies: IOS-070, IOS-033.
  - Add policy-versioned consent, server prompt revisions, review, explicit
    upload action, progress, revoke/delete, and collection completeness.
  - Acceptance: feature is absent when off; consent and deletion UI tests fail
    closed; ordinary transcription never creates an example.
  - Evidence: `TBD`

- [ ] **IOS-072 — Background example upload queue**
  - Dependencies: IOS-071.
  - Add user-scoped, idempotent, protected background transfers with relaunch
    reconciliation and explicit local/server deletion state.
  - Acceptance: tests cover suspension, retry, duplicate callback, sign-out,
    revoke, delete race, and orphan cleanup.
  - Evidence: `TBD`

- [ ] **IOS-073 — Training status and model activation**
  - Dependencies: IOS-070, IOS-072.
  - Show dataset status, held-out metrics, job state, version, activation,
    rollback, and deletion without overstating model quality.
  - Acceptance: deterministic contract/UI tests cover every terminal state;
    activation is impossible without a completed evaluated model.
  - Evidence: `TBD`

## Deferred, explicitly outside this queue

- On-device model conversion and native face alignment.
- macOS capture and distribution.
- External TestFlight or App Store release.
- General-population training-data contribution.
- Live continuous camera transcription.
