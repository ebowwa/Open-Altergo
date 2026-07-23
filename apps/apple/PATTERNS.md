# Adopted Apple development patterns

This plan was derived from the repository owner's existing Apple projects and
git history. It captures repeatable behavior without copying private account
identifiers, paths, endpoints, or credentials into this public repository.

## Patterns adopted

### CLI-first, artifact-driven development

Build and test with direct `xcodebuild` commands wrapped by small repository
scripts. Claude Code runs the command, reads the log and `.xcresult`, opens
current screenshots, fixes the issue, and reruns. There is no separate service
that invokes a Claude API.

### Declarative project definition

Keep an agent-reviewable `project.yml` and generate the Xcode project. This
reduces project-file merge noise and makes configuration changes visible.
Generated project files are checked for determinism and are never hand-edited.

### Small evidence-backed commits

Use bounded conventional commits. CI, signing, tooling, test, and app behavior
fixes remain separable. A commit is not complete merely because code was
written; it records the test or artifact that demonstrated the result.

### `main` plus explicit release signal

`main` is the source of truth. A reviewed commit is released by advancing a
dedicated `bump` branch or by an explicitly approved dispatch. Build numbers
come from CI and App Store Connect is polled for the exact upload.

### Existing self-hosted signing state

On the trusted team Mac, reuse the existing signing identity and shared
keychain. Materialize the App Store Connect key only for the release step,
remove it unconditionally, and avoid exporting a `.p12` when the build stays on
the same controlled machine.

### Doppler for release secrets

Keep GitHub secrets minimal. A short-lived Doppler credential unlocks the
specific App Store Connect material needed by the release job. Operational
identifiers remain variables, not literals spread through scripts.

### Custom REST helpers over a large release dependency

Use compact GitHub/App Store Connect REST helpers for dispatch, run lookup,
watching, and build-processing status. Fastlane-compatible screenshot folders
are useful, but Fastlane is not required to own the build or TestFlight upload.

### Fail-closed automation

Verify current state before acting. A release must prove branch ancestry,
signing identity, bundle identity, build number, upload response, and processed
state. Missing evidence is a blocker, not success.

### Documentation as an execution system

Keep architecture, API, testing, release, and ordered tasks beside the app.
Each task has dependencies, acceptance criteria, and required evidence so an
agent can resume without reconstructing intent from chat history.

## Patterns intentionally not copied

- Hard-coded `/Users/<name>/...` paths.
- Deleting all global DerivedData.
- Pulling or mutating unrelated dependency repositories during a build.
- Placeholder signing values inside release scripts.
- Long-lived private keys written into the checkout.
- A `.p12` export when an existing controlled runner already has the identity.
- Running public fork code on a credentialed self-hosted runner.
- A monolithic workflow that mixes PR tests, screenshots, signing, and upload.
- Fastlane as a mandatory abstraction over transparent `xcodebuild` and ASC
  operations.
- Claims that a simulator tested physical camera behavior.
- Success reports based only on an archive, without ASC processing evidence.

## Intentional improvement for this repository

Some existing projects can safely use one self-hosted workflow because their
source is private. Open-Altergo is public, so this plan separates secret-free
GitHub-hosted pull-request checks from the protected release Mac. That
difference is a security requirement, not a stylistic preference.
