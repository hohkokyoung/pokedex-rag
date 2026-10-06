#!/usr/bin/env bash
# Stop hook: Claude Code can't end a turn while the code it changed fails lint/tests.
#
#   backend *.py changed  -> ruff + pytest (needs the Compose DB on :5433)
#   frontend *.ts(x)      -> tsc --noEmit + eslint
#
# Silent when green or when nothing changed since the last green run (fingerprint of
# the uncommitted diff), so chat-only turns cost nothing. On failure it blocks with a
# short tail of the output. After 3 blocked stops in a row it lets the turn end, so an
# unfixable failure can't loop forever — Claude must then report it.
set -uo pipefail

input=$(cat)
session=$(jq -r '.session_id // "x"' <<<"$input")
retrying=$(jq -r '.stop_hook_active // false' <<<"$input")

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}" || exit 0
state="${TMPDIR:-/tmp}/pokerag-verify"
mkdir -p "$state"

fingerprint() {  # uncommitted changes (tracked + untracked) under the given pathspecs
  { git diff HEAD -- "$@"; git ls-files --others --exclude-standard -z -- "$@" | xargs -0 cat 2>/dev/null; } | shasum | cut -c1-16
}
changed() { [ -n "$(git status --porcelain -- "$@")" ]; }

be_specs=('backend/*.py')
fe_specs=('frontend/*.ts' 'frontend/*.tsx')
failures=""
notes=""

run() {  # run <label> <dir> <cmd...> ; appends a tail of output on failure
  local label=$1 dir=$2; shift 2
  local out
  if ! out=$(cd "$dir" && "$@" 2>&1); then
    failures+=$'\n'"── $label failed ──"$'\n'"$(tail -n 40 <<<"$out")"$'\n'
  fi
}

if changed "${be_specs[@]}"; then
  fp=$(fingerprint "${be_specs[@]}")
  if [ "$(cat "$state/backend" 2>/dev/null)" != "$fp" ]; then
    before=$failures
    run "ruff" backend uv run ruff check .
    if nc -z localhost 5433 2>/dev/null; then
      run "pytest" backend env DATABASE_URL="postgresql+asyncpg://pokedex:pokedex@localhost:5433/pokedex" \
        uv run pytest -q -x --tb=short --no-header
    else
      notes+="verify: DB not running on :5433 — backend tests skipped (run make up). "
      fp=""  # don't record green without tests
    fi
    [ "$failures" = "$before" ] && [ -n "$fp" ] && echo "$fp" >"$state/backend"
  fi
fi

if changed "${fe_specs[@]}"; then
  fp=$(fingerprint "${fe_specs[@]}")
  if [ "$(cat "$state/frontend" 2>/dev/null)" != "$fp" ]; then
    before=$failures
    run "tsc" frontend npx tsc --noEmit
    run "eslint" frontend npx eslint .
    [ "$failures" = "$before" ] && echo "$fp" >"$state/frontend"
  fi
fi

count_file="$state/blocks-$session"
if [ -z "$failures" ]; then
  rm -f "$count_file"
  [ -n "$notes" ] && jq -n --arg m "$notes" '{systemMessage: $m}'
  exit 0
fi

[ "$retrying" = "true" ] || rm -f "$count_file"
n=$(( $(cat "$count_file" 2>/dev/null || echo 0) + 1 ))
echo "$n" >"$count_file"
if [ "$n" -gt 3 ]; then
  rm -f "$count_file"
  jq -n '{systemMessage: "verify: checks still failing after 3 attempts — stopping; report the failure."}'
  exit 0
fi

echo "Checks failed — fix them, or if they can't be fixed, say so plainly in your reply.${failures}" >&2
exit 2
