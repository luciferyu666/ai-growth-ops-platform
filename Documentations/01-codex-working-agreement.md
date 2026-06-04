# Codex Working Agreement

## Collaboration Model

This repository is designed for persistent AI-assisted development sessions.

Codex should:

- Read existing documentation and code before making changes.
- Keep edits scoped to the active task.
- Preserve user-authored changes unless explicitly instructed otherwise.
- Prefer documented decisions over implicit assumptions.
- Verify changes with tests, builds, or focused checks when available.

## Documentation Expectations

Major product, architecture, or compliance decisions should be recorded in `Documentations/decisions/`.

Implementation notes should be concise and written for future maintainers.

## Change Discipline

Each meaningful change should be small enough to review. Broad refactors should be split into separate work items unless they are necessary to complete the current task safely.

## Suggested Session Start Checklist

1. Check `git status`.
2. Read `README.md`.
3. Review the most relevant document in `Documentations/`.
4. Inspect the target files before editing.
5. Run the smallest meaningful verification after changes.
