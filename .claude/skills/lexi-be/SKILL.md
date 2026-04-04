```markdown
# lexi-be Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill outlines the core development patterns and conventions used in the `lexi-be` TypeScript codebase. It covers file naming, import/export styles, commit conventions, and key workflows—especially for adding new ECC bundle components. By following these guidelines, contributors can maintain consistency and quality across the project.

## Coding Conventions

### File Naming

- Use **camelCase** for file names.
  - Example: `userProfile.ts`, `apiClient.ts`

### Imports

- Use **relative import** paths.
  - Example:
    ```typescript
    import { fetchData } from './apiClient';
    ```

### Exports

- Use **named exports** (avoid default exports).
  - Example:
    ```typescript
    // Good
    export function fetchData() { ... }

    // Bad
    export default function fetchData() { ... }
    ```

### Commit Messages

- Follow **Conventional Commits** with the `feat` prefix for features.
  - Example:
    ```
    feat: add user authentication middleware
    ```

## Workflows

### Add ECC Bundle Component
**Trigger:** When you want to introduce or register a new ECC bundle component for `lexi-be-conventions` (such as configuration, skill, agent, or documentation files).
**Command:** `/add-ecc-bundle-component`

1. **Create or add** a new file under the appropriate convention-specific directory. Common directories include:
    - `.claude/`
    - `.agents/`
    - `.codex/`
2. **Example files to add:**
    - `.claude/ecc-tools.json`
    - `.claude/skills/lexi-be/SKILL.md`
    - `.agents/skills/lexi-be/SKILL.md`
    - `.agents/skills/lexi-be/agents/openai.yaml`
    - `.claude/identity.json`
    - `.codex/config.toml`
    - `.codex/AGENTS.md`
    - `.codex/agents/explorer.toml`
    - `.codex/agents/reviewer.toml`
    - `.codex/agents/docs-researcher.toml`
    - `.claude/homunculus/instincts/inherited/lexi-be-instincts.yaml`
    - `.claude/commands/refactoring.md`
3. **Commit** your changes with a message indicating the addition to the ECC bundle, following the conventional commit format:
    ```
    feat: add [component] to ECC bundle
    ```
4. **Push** your changes and open a pull request if required.

#### Example

```bash
# Add a new skill markdown
touch .claude/skills/lexi-be/SKILL.md

# Commit with a conventional message
git add .claude/skills/lexi-be/SKILL.md
git commit -m "feat: add SKILL.md for lexi-be ECC bundle"
git push
```

## Testing Patterns

- **Test files** follow the `*.test.*` naming pattern (e.g., `userProfile.test.ts`).
- **Testing framework** is not explicitly detected; check existing test files for patterns.
- Place tests alongside source files or in a dedicated test directory as per project structure.

#### Example

```typescript
// userProfile.test.ts
import { getUserProfile } from './userProfile';

test('returns correct user profile', () => {
  expect(getUserProfile('123')).toEqual({ id: '123', name: 'Alice' });
});
```

## Commands

| Command                     | Purpose                                                        |
|-----------------------------|----------------------------------------------------------------|
| /add-ecc-bundle-component   | Add or register a new ECC bundle component for lexi-be-conventions |
```
