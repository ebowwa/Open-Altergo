# Claude Code loop

Run Claude Code from the repository root on a Mac with Xcode command-line tools
and XcodeGen available. Paste this prompt:

```text
You are implementing the native iOS client for Open-Altergo.

First read:
- apps/apple/CLAUDE.md
- apps/apple/README.md
- apps/apple/IMPLEMENTATION_PLAN.md
- apps/apple/API.md
- apps/apple/TESTING.md
- apps/apple/RELEASE.md
- apps/apple/PATTERNS.md
- apps/apple/TASKS.md

Treat those files and the checked-in Python HTTP API/tests as the specification.
Check the worktree and preserve unrelated changes. Select the first unchecked
TASKS.md item whose dependencies are complete. Announce that single task and
its acceptance criteria, implement it, generate the project when required, run
the narrowest relevant tests and then the full Apple test command, inspect the
actual logs/xcresult/screenshots, fix failures, and rerun until green.

Update the task's Evidence line with exact commands and artifact paths. Mark it
complete only when every acceptance criterion is demonstrated. Make one
conventional commit for the completed task with:
Co-Authored-By: Claude <noreply@anthropic.com>

Then continue to the next unblocked task. Do not hand-edit the generated Xcode
project, delete global DerivedData, add microphone capture, expose secrets,
invent missing server endpoints, run fork PR code on the self-hosted release
runner, or report a physical-device/TestFlight check that was not actually
performed.

Stop with a precise blocker and the smallest needed human action if the next
task requires an unavailable Apple account decision, bundle ID, production
endpoint, signing state, physical iPhone, missing backend contract, or release
authorization. Do not replace those gates with shipping placeholders.
```

Useful startup check:

```bash
git status --short
xcodebuild -version
xcode-select -p
xcrun simctl list devices available
xcodegen version
```

The loop is intentionally task-driven rather than time-driven. Rerunning the
same prompt resumes at the first unchecked, dependency-complete task.
