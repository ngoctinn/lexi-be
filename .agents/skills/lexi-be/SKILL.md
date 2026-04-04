```markdown
# lexi-be Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill teaches you the core development patterns, coding conventions, and workflows used in the `lexi-be` Python codebase. You'll learn how to structure your code, write and commit changes, update infrastructure and documentation, and manage ECC bundle components in line with the team's established practices.

---

## Coding Conventions

The `lexi-be` repository follows clear and consistent coding standards to ensure maintainability and readability.

### File Naming

- **Style:** `snake_case`
- **Example:**  
  ```
  user_profile.py
  auth_handler.py
  ```

### Import Style

- **Relative imports** are preferred within the package.
- **Example:**
  ```python
  from .models import User
  from ..utils import hash_password
  ```

### Export Style

- **Named exports** are used; avoid wildcard (`*`) exports.
- **Example:**
  ```python
  # In user_profile.py
  class UserProfile:
      ...
  
  def get_user_profile(user_id):
      ...
  ```

### Commit Messages

- **Types:** Mixed (features, refactors, etc.)
- **Prefixes:** `feat`, `refactor`
- **Average Length:** ~55 characters
- **Example:**
  ```
  feat: add JWT authentication to user login
  refactor: move profile logic to separate module
  ```

---

## Workflows

### Feature Development with Merge

**Trigger:** When implementing a new feature or refactoring a major component to be merged into main.  
**Command:** `/feature-dev`

1. **Create a feature or refactor branch.**
2. **Implement changes** across relevant files (e.g., domain, application, infrastructure, handlers).
3. **Commit changes** with a descriptive message.
4. **Open a pull request** and merge into main.

**Files Involved:**
- `src/application/use_cases/auth/*.py`
- `src/domain/entities/*.py`
- `src/infrastructure/handlers/auth/*.py`
- `src/infrastructure/persistence/*.py`
- `src/handlers/auth/*.py`
- `src/handlers/profile/app.py`
- `template.yaml`
- `docs/SRS.md`
- `config/database.yaml`

**Example:**
```bash
git checkout -b feat/add-user-profile
# Make code changes
git add src/domain/entities/user_profile.py
git commit -m "feat: add user profile entity"
git push origin feat/add-user-profile
# Open PR and merge
```

---

### AWS Infrastructure Update

**Trigger:** When updating AWS Lambda, Cognito, or DynamoDB infrastructure.  
**Command:** `/infra-update`

1. **Edit or add YAML files** for Lambda functions or Cognito.
2. **Update infrastructure/template.yaml** or `template.yaml`.
3. **Optionally update** `samconfig.toml`.
4. **Commit changes.**

**Files Involved:**
- `infrastructure/functions/*.yaml`
- `infrastructure/template.yaml`
- `template.yaml`
- `infra/functions/*.yaml`
- `infra/cognito.yaml`
- `samconfig.toml`

**Example:**
```bash
# Edit infrastructure/template.yaml
git add infrastructure/template.yaml
git commit -m "feat: add new Lambda for user notifications"
git push
```

---

### Documentation Update (SRS)

**Trigger:** When updating the Software Requirements Specification or related docs.  
**Command:** `/update-docs`

1. **Edit** `docs/SRS.md` or `docs/database.md`.
2. **Commit changes** with a documentation-related message.

**Files Involved:**
- `docs/SRS.md`
- `docs/database.md`

**Example:**
```bash
# Edit docs/SRS.md
git add docs/SRS.md
git commit -m "docs: update SRS for new auth flow"
git push
```

---

### ECC Bundle Component Addition and Revert

**Trigger:** When adding or removing an ECC bundle component (agent, skill, config, etc.) for the Lexi-BE agent ecosystem.  
**Command:** `/add-ecc-bundle`

1. **Add or update files** in `.claude/commands`, `.claude/skills`, `.claude/ecc-tools.json`, `.codex/agents`, `.agents/skills`, etc.
2. **Commit each file addition** with a descriptive message.
3. **Optionally revert** by removing or restoring the same set of files.
4. **Merge the changes.**

**Files Involved:**
- `.claude/commands/*.md`
- `.claude/skills/lexi-be/SKILL.md`
- `.claude/ecc-tools.json`
- `.claude/identity.json`
- `.claude/homunculus/instincts/inherited/lexi-be-instincts.yaml`
- `.codex/AGENTS.md`
- `.codex/agents/*.toml`
- `.codex/config.toml`
- `.agents/skills/lexi-be/SKILL.md`
- `.agents/skills/lexi-be/agents/openai.yaml`

**Example:**
```bash
git add .claude/skills/lexi-be/SKILL.md
git commit -m "feat: add SKILL.md for new ECC bundle"
git push
# To revert:
git rm .claude/skills/lexi-be/SKILL.md
git commit -m "refactor: remove ECC bundle skill"
git push
```

---

## Testing Patterns

- **Framework:** Unknown (not detected)
- **Test File Pattern:** `*.test.ts` (suggests some TypeScript tests, possibly for infrastructure or integration)
- **Note:** Python code may not have dedicated test files in this repo, or tests may be external.

---

## Commands

| Command         | Purpose                                                    |
|-----------------|-----------------------------------------------------------|
| /feature-dev    | Start a new feature or refactor workflow                  |
| /infra-update   | Update AWS infrastructure (Lambda, Cognito, DynamoDB, etc.)|
| /update-docs    | Update SRS or related documentation                       |
| /add-ecc-bundle | Add or revert an ECC bundle component                     |
```
