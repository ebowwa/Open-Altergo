#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPOSITORY_ID="simonlesaumon/lrs3-lipreader-visual-only"
REVISION="${1:-}"

if ! [[ "$REVISION" =~ ^[0-9a-fA-F]{40}$ ]]; then
  printf 'Usage: %s <40-character-hugging-face-commit>\n' "$0" >&2
  exit 2
fi

command -v hf >/dev/null 2>&1 || {
  printf 'The Hugging Face hf CLI is required.\n' >&2
  printf 'Install instructions: https://huggingface.co/docs/huggingface_hub/guides/cli\n' >&2
  exit 1
}

DESTINATION="$REPO_ROOT/pretraining/.cache/lrs3-lipreader-visual-only/$REVISION"
mkdir -p "$DESTINATION"

printf 'Downloading %s at immutable revision %s\n' \
  "$REPOSITORY_ID" "$REVISION"
hf download "$REPOSITORY_ID" \
  --repo-type model \
  --revision "$REVISION" \
  --local-dir "$DESTINATION"

CHECKSUM_FILE="$DESTINATION/SHA256SUMS"
: >"$CHECKSUM_FILE"

while IFS= read -r file; do
  relative_path="${file#"$DESTINATION/"}"
  test "$relative_path" = "SHA256SUMS" && continue
  hash="$(shasum -a 256 "$file" | awk '{print $1}')"
  printf '%s  %s\n' "$hash" "$relative_path" >>"$CHECKSUM_FILE"
done < <(
  find "$DESTINATION" -type f -not -path "$DESTINATION/.cache/*" -print |
    LC_ALL=C sort
)

printf 'Downloaded files and generated checksums:\n%s\n' "$CHECKSUM_FILE"
printf 'Do not commit the downloaded directory. Review and pin source.json.\n'
