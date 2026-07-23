#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"

DOPPLER_PROJECT="${DOPPLER_PROJECT:-seed}"
DOPPLER_CONFIG="${DOPPLER_CONFIG:-prd}"
CLAUDE_PERMISSION_MODE="${CLAUDE_PERMISSION_MODE:-bypassPermissions}"
CLAUDE_MAX_TURNS="${CLAUDE_MAX_TURNS:-100}"
CLAUDE_LOOP_MAX_PASSES="${CLAUDE_LOOP_MAX_PASSES:-50}"
CLAUDE_LOOP_MAX_STALLED="${CLAUDE_LOOP_MAX_STALLED:-2}"
CLAUDE_MODEL="${CLAUDE_MODEL:-}"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: apps/apple/scripts/claude-loop.sh [options]

Run the Open-Altergo iOS task queue through Claude Code and Doppler.

Options:
  --project NAME          Doppler project (default: seed)
  --config NAME           Doppler config (default: prd)
  --permission-mode MODE  Claude permission mode (default: bypassPermissions)
  --model MODEL           Optional Claude model name or ID
  --max-turns N           Agentic turns allowed per pass (default: 100)
  --max-passes N          Claude processes allowed in this run (default: 50)
  --max-stalled N         Stop after N passes without repository progress
                           (default: 2)
  --dry-run               Print the resolved invocation without starting Claude
  -h, --help              Show this help

Environment variables with the same uppercase names may also set every option.

Examples:
  apps/apple/scripts/claude-loop.sh
  CLAUDE_MODEL=opus apps/apple/scripts/claude-loop.sh
  apps/apple/scripts/claude-loop.sh --max-passes 10 --max-turns 60
EOF
}

die() {
  printf 'claude-loop: %s\n' "$*" >&2
  exit 1
}

require_positive_integer() {
  case "$2" in
    ''|*[!0-9]*|0)
      die "$1 must be a positive integer; received '$2'"
      ;;
  esac
}

while (($# > 0)); do
  case "$1" in
    --project)
      (($# >= 2)) || die "--project requires a value"
      DOPPLER_PROJECT="$2"
      shift 2
      ;;
    --config)
      (($# >= 2)) || die "--config requires a value"
      DOPPLER_CONFIG="$2"
      shift 2
      ;;
    --permission-mode)
      (($# >= 2)) || die "--permission-mode requires a value"
      CLAUDE_PERMISSION_MODE="$2"
      shift 2
      ;;
    --model)
      (($# >= 2)) || die "--model requires a value"
      CLAUDE_MODEL="$2"
      shift 2
      ;;
    --max-turns)
      (($# >= 2)) || die "--max-turns requires a value"
      CLAUDE_MAX_TURNS="$2"
      shift 2
      ;;
    --max-passes)
      (($# >= 2)) || die "--max-passes requires a value"
      CLAUDE_LOOP_MAX_PASSES="$2"
      shift 2
      ;;
    --max-stalled)
      (($# >= 2)) || die "--max-stalled requires a value"
      CLAUDE_LOOP_MAX_STALLED="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option '$1'; use --help"
      ;;
  esac
done

test -n "$REPO_ROOT" || die "this script must run from an Open-Altergo checkout"
test -f "$REPO_ROOT/apps/apple/CLAUDE.md" ||
  die "apps/apple/CLAUDE.md is missing"
test -f "$REPO_ROOT/apps/apple/TASKS.md" ||
  die "apps/apple/TASKS.md is missing"

require_positive_integer "CLAUDE_MAX_TURNS" "$CLAUDE_MAX_TURNS"
require_positive_integer "CLAUDE_LOOP_MAX_PASSES" "$CLAUDE_LOOP_MAX_PASSES"
require_positive_integer "CLAUDE_LOOP_MAX_STALLED" "$CLAUDE_LOOP_MAX_STALLED"

case "$CLAUDE_PERMISSION_MODE" in
  default|acceptEdits|plan|auto|dontAsk|bypassPermissions)
    ;;
  *)
    die "unsupported Claude permission mode '$CLAUDE_PERMISSION_MODE'"
    ;;
esac

PROMPT="$(cat <<'EOF'
Implement the native iOS client from the checked-in Open-Altergo execution
queue.

Read apps/apple/CLAUDE.md first, then every document it requires. Treat
apps/apple/TASKS.md and the checked-in Python HTTP API/tests as the executable
specification.

Work on the first unchecked task whose dependencies are complete. Any dirty
files left by an earlier claude-loop pass belong to this loop unless the
worktree shows clearly unrelated user changes; resume your own incomplete work
and preserve unrelated changes. Complete one bounded task, generate the project
when needed, test it, inspect actual logs/xcresult/screenshots, update its
Evidence line, mark it complete only with evidence, and make its conventional
commit. Continue within this pass while context and turn budget permit.

Do not push, upload to TestFlight, change external state, invent a missing
backend, expose secrets, or claim tests you did not run.
Stop at a documented human, physical-device, Apple-account, signing, endpoint,
or release-authorization gate.

Your final output must end with exactly one line in one of these forms:

LOOP_STATUS: CONTINUE
LOOP_STATUS: COMPLETE
LOOP_STATUS: BLOCKED - <smallest human action needed>

Use COMPLETE only when no unchecked IOS task remains. Use CONTINUE when you
made repository progress and another unblocked task can run. Use BLOCKED when
the next incomplete task cannot proceed autonomously.
EOF
)"

print_invocation() {
  printf 'Repository: %s\n' "$REPO_ROOT"
  printf 'Doppler:    project=%s config=%s\n' \
    "$DOPPLER_PROJECT" "$DOPPLER_CONFIG"
  printf 'Claude:     permission=%s max-turns=%s' \
    "$CLAUDE_PERMISSION_MODE" "$CLAUDE_MAX_TURNS"
  if test -n "$CLAUDE_MODEL"; then
    printf ' model=%s' "$CLAUDE_MODEL"
  fi
  printf '\n'
  printf 'Limits:     passes=%s stalled=%s\n' \
    "$CLAUDE_LOOP_MAX_PASSES" "$CLAUDE_LOOP_MAX_STALLED"
  if test "$CLAUDE_PERMISSION_MODE" = "bypassPermissions"; then
    printf 'Command:    doppler run -p %s -c %s -- claude -p %s ...\n' \
      "$DOPPLER_PROJECT" \
      "$DOPPLER_CONFIG" \
      "--dangerously-skip-permissions"
  else
    printf 'Command:    doppler run -p %s -c %s -- claude -p %s %s ...\n' \
      "$DOPPLER_PROJECT" \
      "$DOPPLER_CONFIG" \
      "--permission-mode" \
      "$CLAUDE_PERMISSION_MODE"
  fi
}

if ((DRY_RUN)); then
  print_invocation
  exit 0
fi

command -v doppler >/dev/null 2>&1 || die "doppler is not installed or not in PATH"
command -v claude >/dev/null 2>&1 || die "claude is not installed or not in PATH"

cd "$REPO_ROOT"

LOG_ROOT="$REPO_ROOT/apps/apple/.build/claude-loop"
LOCK_DIR="$LOG_ROOT/active.lock"
mkdir -p "$LOG_ROOT"
chmod 700 "$LOG_ROOT"
umask 077

cleanup_lock() {
  if test -f "$LOCK_DIR/pid"; then
    rm -f "$LOCK_DIR/pid"
  fi
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  if test -f "$LOCK_DIR/pid"; then
    ACTIVE_PID="$(sed -n '1p' "$LOCK_DIR/pid" 2>/dev/null || true)"
    case "$ACTIVE_PID" in
      ''|*[!0-9]*)
        ;;
      *)
        if kill -0 "$ACTIVE_PID" 2>/dev/null; then
          die "another loop is active with PID $ACTIVE_PID"
        fi
        ;;
    esac
  fi
  cleanup_lock
  mkdir "$LOCK_DIR" || die "could not acquire loop lock at $LOCK_DIR"
fi
printf '%s\n' "$$" >"$LOCK_DIR/pid"
trap cleanup_lock EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

printf 'Checking Doppler access without printing secrets...\n'
doppler run -p "$DOPPLER_PROJECT" -c "$DOPPLER_CONFIG" -- true ||
  die "Doppler could not access $DOPPLER_PROJECT/$DOPPLER_CONFIG"

print_invocation
if test "$CLAUDE_PERMISSION_MODE" = "bypassPermissions"; then
  printf '%s\n' \
    'WARNING: Claude permission checks are disabled for this repository session.' \
    'Claude can execute shell commands, edit files, access Doppler-injected' \
    'environment variables, and affect systems reachable from this Mac.'
fi

remaining_tasks() {
  grep -Ec '^- \[ \] \*\*IOS-' apps/apple/TASKS.md 2>/dev/null || true
}

state_signature() {
  {
    git rev-parse HEAD
    git status --porcelain=v1 --untracked-files=all
    shasum -a 256 apps/apple/TASKS.md
  } | shasum -a 256 | awk '{print $1}'
}

stalled=0
pass=1

while ((pass <= CLAUDE_LOOP_MAX_PASSES)); do
  before_remaining="$(remaining_tasks)"
  if ((before_remaining == 0)); then
    printf 'All IOS tasks are complete.\n'
    exit 0
  fi

  before_signature="$(state_signature)"
  timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
  log_file="$LOG_ROOT/pass-$(printf '%03d' "$pass")-$timestamp.log"

  printf '\nPass %d/%d — %d IOS tasks remain\n' \
    "$pass" "$CLAUDE_LOOP_MAX_PASSES" "$before_remaining"
  printf 'Local transcript: %s\n' "$log_file"

  claude_args=(
    -p
    --output-format text
    --max-turns "$CLAUDE_MAX_TURNS"
  )
  if test "$CLAUDE_PERMISSION_MODE" = "bypassPermissions"; then
    claude_args+=(--dangerously-skip-permissions)
  else
    claude_args+=(--permission-mode "$CLAUDE_PERMISSION_MODE")
  fi
  if test -n "$CLAUDE_MODEL"; then
    claude_args+=(--model "$CLAUDE_MODEL")
  fi
  claude_args+=("$PROMPT")

  set +e
  doppler run \
    -p "$DOPPLER_PROJECT" \
    -c "$DOPPLER_CONFIG" \
    -- claude "${claude_args[@]}" 2>&1 | tee "$log_file"
  claude_status="${PIPESTATUS[0]}"
  set -e

  if ((claude_status != 0)); then
    printf 'Claude exited with status %d; see %s\n' \
      "$claude_status" "$log_file" >&2
    exit "$claude_status"
  fi

  status_line="$(
    grep -E 'LOOP_STATUS: (CONTINUE|COMPLETE|BLOCKED)' "$log_file" |
      tail -n 1 || true
  )"
  after_remaining="$(remaining_tasks)"
  after_signature="$(state_signature)"

  case "$status_line" in
    *"LOOP_STATUS: BLOCKED"*)
      printf '%s\n' "$status_line"
      exit 2
      ;;
    *"LOOP_STATUS: COMPLETE"*)
      if ((after_remaining == 0)); then
        printf 'Claude completed the IOS task queue.\n'
        exit 0
      fi
      printf 'Claude reported COMPLETE, but %d IOS tasks remain; stopping.\n' \
        "$after_remaining" >&2
      exit 3
      ;;
  esac

  if test "$before_signature" = "$after_signature"; then
    stalled=$((stalled + 1))
    printf 'No repository progress detected in pass %d (%d/%d stalled).\n' \
      "$pass" "$stalled" "$CLAUDE_LOOP_MAX_STALLED" >&2
  else
    stalled=0
    printf 'Progress: %d -> %d remaining IOS tasks.\n' \
      "$before_remaining" "$after_remaining"
  fi

  if ((stalled >= CLAUDE_LOOP_MAX_STALLED)); then
    printf 'Stopping after %d passes without repository progress.\n' \
      "$stalled" >&2
    printf 'Inspect the latest transcript: %s\n' "$log_file" >&2
    exit 4
  fi

  pass=$((pass + 1))
done

printf 'Reached the configured maximum of %d passes with %d IOS tasks left.\n' \
  "$CLAUDE_LOOP_MAX_PASSES" "$(remaining_tasks)" >&2
exit 5
