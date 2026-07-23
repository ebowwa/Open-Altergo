# Claude Code instructions for the Apple client

These instructions apply to every file under `apps/apple`.

## Mission

Implement the iOS client described by the documents in this directory. Work in
small, verified increments until the first unblocked item in `TASKS.md` is
complete. Continue to the next item only when the current item satisfies its
acceptance criteria and evidence requirements.

Read, in order:

1. `README.md`
2. `IMPLEMENTATION_PLAN.md`
3. `API.md`
4. `TESTING.md`
5. `RELEASE.md`
6. `TASKS.md`

The checked-in Python HTTP API and its tests are the source of truth when they
disagree with prose.

## Operating loop

For every task:

1. Check `git status --short`. Preserve unrelated user changes.
2. Confirm all dependency task IDs are complete.
3. State the one task being implemented and its acceptance criteria.
4. Make the smallest coherent change that completes it.
5. Generate the Xcode project if `project.yml` changed.
6. Run the narrowest relevant test, then the full Apple test command.
7. Inspect failures, `.xcresult`, logs, and screenshots directly.
8. Fix the cause and rerun. Never weaken an assertion merely to get green.
9. Update the task checkbox and its evidence line with the command and artifact.
10. Commit one conventional, reviewable change.
11. Repeat until blocked or until the requested phase is complete.

Claude Code itself runs the commands and reads the resulting artifacts. Do not
create a second program that calls a Claude API, do not start nested agents, and
do not claim visual correctness without inspecting the current screenshots.

## Build rules

- Use native SwiftUI and AVFoundation.
- Use Swift 6 strict concurrency.
- Deployment target is iOS 17 unless an explicit decision changes it.
- `project.yml` is the project source of truth.
- Never hand-edit a generated `.xcodeproj`.
- Keep DerivedData below `apps/apple/.build/DerivedData`.
- Never delete global `~/Library/Developer/Xcode/DerivedData`.
- Use `xcodebuild`, not Xcode UI automation, for repeatable checks.
- Keep the runtime dependency-free initially. Prefer Foundation, SwiftUI,
  AVFoundation, PhotosUI, Security, OSLog, and SwiftData.
- Do not add a Swift package just to make folders look architectural.
- Keep the iOS target compiling after every commit.

## Architecture rules

- Views render state and send actions; they do not perform networking or file
  management.
- Inject protocols for API, capture, persistence, credentials, and time.
- Put mutable network and persistence coordination behind actors.
- Do not introduce global business-state singletons.
- Stream file uploads from disk. Do not load a potentially 250 MB video into
  one `Data` value.
- Store credentials in Keychain, never `UserDefaults`.
- Store only non-secret settings such as a development server URL in app
  preferences.
- Temporary media must have one owner and deterministic cleanup on success,
  failure, cancellation, and relaunch recovery.
- UI-visible errors must be typed and actionable. Logs may contain request IDs
  and durations, but never video bytes, transcript text, expected text, tokens,
  or authorization headers.

## Privacy and safety rules

- Request camera permission only when the user starts capture.
- Do not request microphone permission and do not add an audio input.
- Do not silently upload, retain, or reuse a clip.
- Never turn ordinary transcripts or corrections into training examples.
- Personalization stays feature-flagged until its authenticated endpoints,
  deletion behavior, and consent tests exist.
- Development HTTP exceptions belong in Debug configuration only. Release must
  use HTTPS and App Transport Security.
- Fail closed when authentication, consent, file protection, or deletion state
  is uncertain.

## Testing and evidence

- Unit and contract tests run without a live model or network.
- UI tests use injected deterministic fixtures and stable accessibility IDs.
- Save screenshot evidence to the path defined in `TESTING.md`.
- Never report camera behavior as verified from the simulator. Run the physical
  device checklist and record device/OS evidence.
- Never report TestFlight success because archive export succeeded. Verify the
  upload reaches App Store Connect processing and record the build number.
- A test that was not run must be reported as not run.

## Git and release discipline

- Conventional commit prefixes: `feat:`, `fix:`, `test:`, `ci:`, `docs:`,
  `refactor:`, `build:`, or `tools:`.
- Keep commits bounded to one task or one directly related fix.
- Add `Co-Authored-By: Claude <noreply@anthropic.com>` when Claude authored the
  change.
- Do not rewrite shared history.
- Do not push, create releases, alter signing, or upload to TestFlight unless
  the active task and user authorization explicitly include that action.
- `main` is the source branch. Advancing `bump` to a reviewed `main` commit is
  the intentional TestFlight release signal.
- Never run untrusted public pull-request code on the self-hosted signing
  runner.

## Stop conditions

Stop and report a precise blocker when:

- the next task needs an Apple account choice, bundle ID, endpoint, or product
  decision that is not recorded;
- signing or App Store Connect state cannot be checked safely;
- a required physical device is unavailable;
- a server endpoint required by the task does not exist;
- an unrelated dirty-worktree change overlaps the files that must be edited; or
- a command would expose or destroy user data.

Do not paper over the blocker with placeholders in shipping code. Planning
documents may use explicit `TBD` fields when the corresponding task owns their
resolution.
