---
name: feature-development-with-merge
description: Workflow command scaffold for feature-development-with-merge in lexi-be.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /feature-development-with-merge

Use this workflow when working on **feature-development-with-merge** in `lexi-be`.

## Goal

Implements a new feature or refactors a major component, followed by a merge commit. This workflow typically involves making a set of related code changes and then merging them into the main branch.

## Common Files

- `src/application/use_cases/auth/*.py`
- `src/domain/entities/*.py`
- `src/infrastructure/handlers/auth/*.py`
- `src/infrastructure/persistence/*.py`
- `src/handlers/auth/*.py`
- `src/handlers/profile/app.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create a feature or refactor branch.
- Implement changes across multiple related files (domain, application, infrastructure, handlers, etc.).
- Commit the changes with a descriptive message.
- Open a pull request and merge into main.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.