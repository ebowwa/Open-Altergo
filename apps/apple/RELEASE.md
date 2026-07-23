# Apple CI, signing, and TestFlight

## 1. Trust model

Open-Altergo is public. Pull requests from forks are untrusted and must never
execute on a persistent self-hosted Mac that has signing identities, a Doppler
token, App Store Connect credentials, or access to other repositories.

Split automation:

```text
public PR / main push
    └── GitHub-hosted macOS, no secrets, unsigned build and tests

trusted bump push / approved manual dispatch
    └── self-hosted macOS ARM64, protected environment, signing and TestFlight
```

Do not use `pull_request_target` to build or execute contributor code. Protect
the `apple-release` GitHub Environment with required reviewers. Release jobs
check that the requested SHA is reachable from `origin/main`.

## 2. Workflows to create

### `apple-ci.yml`

Triggers:

- pull request paths affecting Apple, HTTP API contract, or workflow;
- push to `main` for the same paths; and
- manual dispatch.

Steps:

1. checkout without persisted credentials;
2. select and print Xcode;
3. install a pinned XcodeGen version;
4. generate the project;
5. fail if generation changes tracked files;
6. run Python HTTP contract tests;
7. run unsigned iOS build and tests;
8. collect result bundle, logs, and screenshots; and
9. upload artifacts on failure, with short retention.

This workflow receives no repository secrets.

### `apple-testflight.yml`

Triggers:

- push to branch `bump`; and
- manual dispatch with an explicit `ship` boolean and commit SHA.

Guardrails:

- repository must be `ebowwa/Open-Altergo`;
- SHA must be reachable from `origin/main`;
- GitHub Environment is `apple-release`;
- runner labels include self-hosted, macOS, and ARM64;
- exact `DEVELOPER_DIR` comes from a repository/environment variable;
- workspace is cleaned only within this repository;
- no fork or pull-request event can enter the job.

Steps:

1. checkout the exact trusted SHA;
2. run `doctor.sh` and release preflight;
3. unlock the existing shared team signing keychain on that runner;
4. use a short-lived Doppler token to materialize the App Store Connect `.p8`
   into a permission-restricted temporary directory;
5. generate the project and run release tests;
6. stamp `CFBundleVersion` from `github.run_number`;
7. archive Release with `xcodebuild archive`;
8. export an App Store IPA using generated ExportOptions;
9. upload with an Xcode-supported App Store Connect command;
10. poll App Store Connect until that build is processed or fails;
11. upload IPA, dSYMs, and redacted logs with short retention; and
12. delete the materialized private key in an unconditional cleanup step.

Reuse the signing identity already installed on the trusted Mac. Do not export
and commit or routinely shuttle a `.p12` when the build stays on that machine.

### `apple-screenshots.yml`

Manually or intentionally triggered, secret-free where possible:

- generate the project;
- run screenshot UI tests on named simulator runtimes;
- validate expected files and dimensions;
- upload an artifact; and
- write App Store-compatible images under
  `apps/apple/fastlane/screenshots/en-US`.

Fastlane-compatible paths do not require Fastlane to own builds or uploads.

## 3. Repository settings

Names below are contracts, not checked-in values.

Repository/environment variables:

- `APPLE_BUNDLE_ID`
- `APPLE_TEAM_ID`
- `APPLE_ASC_APP_ID`
- `APPLE_ASC_KEY_ID`
- `APPLE_RELEASE_DEVELOPER_DIR`
- `APPLE_CI_KEYCHAIN_PATH`
- `DOPPLER_PROJECT`
- `DOPPLER_CONFIG`
- `OPEN_ALTERGO_RELEASE_BASE_URL`

Secrets:

- `CI_KEYCHAIN_PASSWORD`
- `DOPPLER_TOKEN`

Doppler supplies:

- `ASC_ISSUER_ID`
- `ASC_AUTH_KEY_<configured key ID>`

Never put a private key, token, profile, certificate, private endpoint, or
developer home path into Git, an `.xcconfig`, an artifact, or a workflow echo.
Team ID, key ID, app ID, and bundle ID are identifiers rather than secrets, but
keeping operational values in environment variables avoids coupling this
public repository to one account.

## 4. Apple account bootstrap

This is a deliberate, partly manual gate:

1. Choose the final bundle ID. A proposed development value is
   `com.ebowwa.openaltergo`; verify availability before adopting it.
2. Register the App ID in the intended Apple Developer team.
3. Create the App Store Connect application with the exact bundle ID.
4. Record the numeric App Store Connect app ID as a protected variable.
5. Confirm Agreements, Tax, and Banking state does not block distribution.
6. Create or choose an App Store Connect API key with only required access.
7. Store issuer and private key in Doppler, never GitHub plaintext.
8. Create App Store distribution provisioning through automatic signing or a
   controlled profile process.
9. Confirm the shared signing keychain identity matches the selected team.
10. Protect `bump`, `main`, and `apple-release` appropriately.

A bundle ID associated with an App Store record is durable identity. Validate
it before wiring entitlements, URLs, or production data around it.

## 5. Versioning

- `CFBundleShortVersionString` is the user-facing semantic release version and
  changes in a reviewed source commit.
- `CFBundleVersion` is CI-owned and equals `github.run_number` for TestFlight.
- Release scripts print version, build, commit SHA, bundle ID, and Xcode version
  before archive.
- The App Store Connect poll uses the exact build number, not merely "latest."

Advancing `bump` to a reviewed `main` commit is the normal release signal:

```bash
git fetch origin
git switch bump
git merge --ff-only origin/main
git push origin bump
```

The helper should refuse a non-fast-forward release and should not force push.
A manual dispatch is for recovery or an intentional one-off and still requires
the same ancestry and environment approval.

## 6. Local release commands

Scripts to create:

```text
scripts/doctor.sh
scripts/generate.sh
scripts/build.sh
scripts/test.sh
scripts/release-preflight.sh
scripts/ci-tools.sh
```

`ci-tools.sh` should use GitHub and App Store Connect REST APIs directly and
should not require the `gh` CLI. Planned commands:

```text
ci-tools.sh dispatch [ref]
ci-tools.sh run-for-sha <sha>
ci-tools.sh watch <run-id>
ci-tools.sh asc [build-number]
```

GitHub authentication can come from the existing Git credential helper.
App Store Connect JWT creation uses the temporary Doppler-provided key. Never
print the JWT or key material.

## 7. App Store readiness

Before internal TestFlight:

- app icon, display name, version, category, support URL, and privacy policy;
- privacy manifest and Required Reason API review;
- accurate App Privacy answers for uploaded video, face imagery, transcript
  text, diagnostics, identifiers, retention, and personalization;
- export-compliance answers;
- camera usage description; no microphone description or entitlement;
- account deletion path if accounts exist;
- in-app deletion consistent with backend retention;
- accessibility review;
- screenshots generated from deterministic UI-test states; and
- reviewer notes explaining silent video capture and server processing.

Before external testing:

- production HTTPS endpoint and authentication;
- rate limiting and abuse controls;
- tested privacy/deletion policy;
- beta review information;
- representative physical-device coverage;
- support/feedback path; and
- an incident response and model rollback path.

TestFlight builds expire after Apple's current retention window. Treat
TestFlight as distribution for testing, not backup storage.

## 8. Distribution boundaries

iOS is distributed through App Store Connect/TestFlight and ultimately the App
Store. A future macOS app needs an explicit decision:

- Mac App Store: sandbox, App Store signing, App Store review; or
- direct: Developer ID signing, hardened runtime, notarization, stapling, update
  distribution, and a separate release workflow.

Do not mix macOS notarization credentials or Sparkle packaging into the iOS
TestFlight workflow.
