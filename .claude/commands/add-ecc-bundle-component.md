---
name: add-ecc-bundle-component
description: Workflow command scaffold for add-ecc-bundle-component in lexi-be.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-ecc-bundle-component

Use this workflow when working on **add-ecc-bundle-component** in `lexi-be`.

## Goal

Adds a new component as part of the lexi-be-conventions ECC bundle, typically introducing new configuration, skill, agent, or documentation files under convention-specific directories.

## Common Files

- `.claude/ecc-tools.json`
- `.claude/skills/lexi-be/SKILL.md`
- `.agents/skills/lexi-be/SKILL.md`
- `.agents/skills/lexi-be/agents/openai.yaml`
- `.claude/identity.json`
- `.codex/config.toml`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create or add a new file under a convention-specific directory (e.g., .claude/, .agents/, .codex/).
- Commit the file with a message indicating addition to the ECC bundle.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.