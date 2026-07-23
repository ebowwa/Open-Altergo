# iOS testing and evidence

## 1. Test layers

### Unit tests

Run on every pull request:

- response and error decoding;
- malformed range rejection;
- multipart byte layout and streamed-file behavior;
- request option validation;
- API error retryability mapping;
- capture and transcription state transitions;
- cancellation;
- file ownership and cleanup;
- orphan purge age boundary;
- history save/update/delete/tombstone behavior;
- Keychain adapter behavior through an injected in-memory fake;
- consent and personalization feature gates;
- log redaction;
- duration, byte, and time formatting; and
- configuration validation.

Tests use deterministic clocks, UUIDs, boundaries, and fixture paths.

### API contract tests

The Python tests remain authoritative for current behavior. Swift tests decode
checked-in JSON fixtures under `Fixtures/API`. CI runs:

```bash
python -m unittest tests.test_http_api
```

and the Swift fixture tests. A later OpenAPI task should generate or validate
fixtures, but generated output never replaces behavioral server tests.

### UI tests

UI tests launch with a fully local mock transport selected by launch arguments.
No UI test depends on the hosted model or public internet.

Required flows:

1. onboarding and privacy explanation;
2. imported-video review to successful result;
3. alternatives and timed segment presentation;
4. no-face guidance and retry;
5. upload progress and cancellation;
6. offline and server-error recovery;
7. history save, reopen, delete one, and delete all;
8. camera denial fallback;
9. retention default;
10. personalization absent when its feature flag is off; and
11. largest Dynamic Type layout for the result flow.

Every control used by UI tests has a semantic accessibility identifier. Do not
locate controls by visible English copy unless the copy itself is the assertion.

### Local integration

On a Mac, start the Python API with a fake service for deterministic contract
checks or the real service for smoke testing:

```bash
uvicorn apis.http_api.app:app --host 0.0.0.0 --port 8000
```

The simulator reaches the Mac using an explicitly configured Debug URL. Real
model smoke tests are opt-in because they can download large assets and consume
GPU/CPU. The checked-in Adam demo video may be used only if its repository
license/provenance permits it and the file is present; tests must skip clearly
rather than fetch private media.

### Physical iPhone

Simulator success does not verify capture. Before internal TestFlight, test on
at least the target iPhone 13 mini and record:

- device model and iOS version;
- camera permission first-run, allow, deny, and later Settings changes;
- front-camera preview orientation;
- saved-file mirroring versus preview mirroring;
- 1-second, 4-second, 40-second, and attempted over-limit clips;
- app backgrounding and interruption during recording;
- phone call/audio-session interruption behavior even though no audio input is
  configured;
- PhotosPicker import from local and iCloud-backed items;
- low storage;
- Wi-Fi and cellular upload;
- offline transition and retry;
- screen lock during upload;
- thermal and memory behavior on repeated clips;
- deletion and relaunch cleanup; and
- absence of microphone permission.

Record what was not testable. Never substitute simulator screenshots for this
checklist.

## 2. Performance requirements

- Multipart creation and upload memory must remain bounded independently of
  video size.
- A 250 MB boundary fixture may be sparse/generated during testing; do not
  commit it.
- The UI remains responsive while configuring capture, copying media, and
  preparing multipart content.
- Repeated capture/transcription cycles do not accumulate temporary files.
- Measure launch, capture readiness, multipart preparation, upload, processing,
  and result rendering with signposts or redacted durations.

Initial thresholds are baselines, not invented promises. Record measurements in
task evidence, then set regression budgets based on observed target hardware.

## 3. Visual evidence loop

UI tests save screenshots to:

```text
apps/apple/.build/screenshots/<test-name>/<step>.png
```

Release-ready App Store images are copied/rendered separately to:

```text
apps/apple/fastlane/screenshots/en-US/
```

The test helper should both:

- attach each screenshot to the `.xcresult`; and
- write it to the deterministic local path so Claude Code can inspect it.

After a UI change, the agent must open the current screenshot files and check
layout, clipping, hierarchy, loading/error states, and privacy-sensitive text.
File existence alone is not visual verification.

## 4. Standard commands

The implementation creates these stable wrappers:

```bash
apps/apple/scripts/doctor.sh
apps/apple/scripts/generate.sh
apps/apple/scripts/build.sh
apps/apple/scripts/test.sh
apps/apple/scripts/test.sh --unit
apps/apple/scripts/test.sh --ui
apps/apple/scripts/test.sh --integration
```

Wrappers must:

- derive the repository path from their own location;
- use `set -euo pipefail`;
- print tool versions and the selected destination;
- use repo-local DerivedData;
- preserve `.xcresult` bundles;
- avoid global cleanup; and
- return nonzero on failure.

The underlying CI command remains visible and reproducible:

```bash
xcodebuild test \
  -project apps/apple/OpenAltergo.xcodeproj \
  -scheme OpenAltergo \
  -configuration Debug \
  -destination 'platform=iOS Simulator,name=iPhone 13 mini,OS=latest' \
  -derivedDataPath apps/apple/.build/DerivedData \
  -resultBundlePath apps/apple/.build/results/OpenAltergo.xcresult \
  CODE_SIGNING_ALLOWED=NO
```

If that simulator is unavailable on the installed Xcode runtime, `doctor.sh`
must print available destinations and fail with an actionable message. CI may
choose another explicitly recorded small iPhone; it must not silently choose
an arbitrary destination.

## 5. CI artifacts

Every failing CI run uploads:

- `.xcresult`;
- build/test logs;
- UI screenshots;
- generated-project consistency diff, if any; and
- crash logs when produced.

Release CI additionally uploads the IPA, dSYMs, export log, and redacted App
Store Connect processing response. Retention is short and intentional because
artifacts may contain product metadata. Test fixtures and logs must never
include user recordings, transcripts, credentials, or private endpoints.

## 6. TestFlight acceptance

An internal build is accepted only when:

- hosted PR CI is green on its source commit;
- release preflight validates branch and clean generated project;
- archive and export succeed;
- App Store Connect acknowledges upload;
- the exact build number reaches a processed state;
- a tester installs it from TestFlight;
- launch, import, one capture, one successful transcription, one no-face
  failure, deletion, and privacy settings are exercised; and
- results are recorded without including sensitive transcript content.
