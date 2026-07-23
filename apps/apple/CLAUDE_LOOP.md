# Claude Code loop

Run Claude Code from the repository root on a Mac with Xcode command-line tools
and XcodeGen available:

```bash
apps/apple/scripts/claude-loop.sh
```

The script uses the same Doppler scope as:

```bash
doppler run -p seed -c prd -- claude
```

It starts Claude in non-interactive print mode, gives each process a bounded
turn budget, and launches another process when Claude reports that an unblocked
task remains. It stops when the queue is complete, a human gate is reached,
Claude exits unsuccessfully, two passes make no repository progress, or the
configured pass limit is reached.

Defaults:

```text
DOPPLER_PROJECT=seed
DOPPLER_CONFIG=prd
CLAUDE_PERMISSION_MODE=bypassPermissions
CLAUDE_MAX_TURNS=100
CLAUDE_LOOP_MAX_PASSES=50
CLAUDE_LOOP_MAX_STALLED=2
```

This disables Claude Code's permission checks. Claude can run shell commands,
edit the checkout, read Doppler-injected environment variables, and act on
systems reachable from the Mac. Run it only from the intended repository on a
machine and account where that access is acceptable. The script still tells
Claude not to push, release, or change external state unless a task is
explicitly authorized, but that is an instruction rather than an enforcement
boundary.

For this default, the wrapper passes Claude Code's
`--dangerously-skip-permissions` flag. Other configured modes use
`--permission-mode`.

Override them with environment variables or command-line options:

```bash
CLAUDE_MODEL=opus \
  apps/apple/scripts/claude-loop.sh --max-passes 10 --max-turns 60
```

Use `--dry-run` to inspect the resolved configuration without contacting
Doppler or starting Claude. Per-pass transcripts are private local files under
`apps/apple/.build/claude-loop/`, which is ignored by Git. The script does not
print Doppler secrets, but Claude's own output can still contain sensitive
material if it ignores the repository rules; review logs before sharing them.

To restore background safety classification instead of bypassing permissions,
use:

```bash
CLAUDE_PERMISSION_MODE=auto \
  apps/apple/scripts/claude-loop.sh
```

Or use `acceptEdits`, which can require additional approval rules for build,
test, and Git commands during a non-interactive run.

## Manual fallback prompt

To run one interactive Claude session instead, start it normally:

```bash
doppler run -p seed -c prd -- claude
```

Then paste:

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

The loop is task-driven rather than time-driven. Rerunning the script resumes
at the first unchecked, dependency-complete task and preserves unfinished work
from a prior pass.
