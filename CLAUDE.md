# CLAUDE.md — LoopForge

## Operating mode

Senior engineer. Code-first, no elisions, no `# ... rest of implementation` placeholders. Minimal commentary — explain a decision only where a reader would otherwise be surprised. If a requirement is ambiguous, ask exactly one clarifying question and stop; do not guess and proceed.

## Plan before code

Every phase begins with a short written plan (files to be created or changed, function signatures, test names) posted for approval. **Do not write implementation code until the plan for that phase is approved.** This applies even to phases that look trivial.

## Stop conditions

Halt immediately and report when any of these occur:

- A phase's tests pass — stop, do not continue into the next phase
- A test fails twice on the same cause after a fix attempt
- A required dependency will not install
- Implementation would require changing a data model in `models.py` — model changes need approval
- Work would touch `ui/` before phase 6 is approved
- You are about to add a dependency not listed in PLAN.md section 8

## Repo discipline

- One commit per phase, message format `phase N: <short description>`
- Never commit without `pytest` green and `ruff check` clean
- Never `git push --force`, never rewrite history, never amend a pushed commit
- Never delete or rewrite a test to make it pass; if a test is wrong, say so and stop

## Boundaries that must not blur

- `spec/` and `report/` are pure: no file I/O, no audio, no Qt imports, no wall-clock time
- `ui/` contains no arithmetic beyond pixel↔second mapping for painting. All musical math lives in `spec/`
- `analysis/` returns a populated `TrackAnalysis` and nothing else — it does not build specs
- Anything a user might want from the CLI must exist in the CLI before it exists in the GUI

## Reporting numbers

Never round a drift, duration, or BPM in output without also stating the residual. The user is checking these against a video model's behaviour and a hidden 40ms error is worse than an ugly number.

## Testing

Synthetic click tracks generated in-process, no audio fixtures committed. Every pure function in `spec/` gets a test including at least one edge case. Assert on values, not on "does not raise".
