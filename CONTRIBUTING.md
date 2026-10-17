# Contributing Guide

Thank you for contributing to this project! This guide is designed so
that even a first-time contributor can make changes safely, while
keeping the repository clean and minimizing merge conflicts.

## 1. Repository Branch Strategy

We use a small set of branch types, each with a clear purpose.

| Branch | Purpose | Example |
| --- | --- | --- |
| `main` | Stable, production-ready code only. Never push directly. | `main` |
| `develop` | Integration branch for completed features and fixes before release. | `develop` |
| `feature/*` | New functionality, enhancements, or restructuring. | `feature/user-authentication` |
| `fix/*` | Bug fixes. Branch from `develop` for normal fixes, or directly from `main` for urgent production issues. | `fix/login-validation` |
| `chore/*` | Everything else: documentation, tests, dependencies, config, and tooling updates. | `chore/update-dependencies` |

### Branch rules

- Do **not** commit directly to `main`.
- Do **not** commit directly to `develop` unless the project
  maintainers explicitly allow it.
- Create a separate branch for every task.
- Keep a branch focused on **one logical change**.
- Never mix unrelated features, formatting changes, dependency
  upgrades, and bug fixes in the same PR.
- For an urgent fix affecting `main`, branch `fix/*` directly from
  `main` instead of `develop`, then merge the fix back into **both**
  `main` and `develop`.
- Delete your branch after its PR has been merged.

---

## 2. Recommended Branch Flow

For normal development:

``` text
main
  │
  └── develop
        │
        ├── feature/your-feature
        ├── fix/your-fix
        └── chore/your-task
```

For an urgent production issue:

``` text
main
  │
  └── fix/critical-fix   (branched directly from main)
```

An urgent fix should be merged back into both `main` and `develop`
when applicable, so the fix does not disappear from future
development.

---

## 3. Before You Start

### Step 1: Fork the Repository

If you are an external contributor:

1.  Fork this repository on GitHub.
2.  Clone your fork locally.
3.  Add the original repository as `upstream`.

``` bash
git clone https://github.com/<your-username>/<repository-name>.git
cd <repository-name>

git remote add upstream https://github.com/<organization-or-owner>/<repository-name>.git
git remote -v
```

If you are already a project collaborator, you can clone the main
repository directly.

### Step 2: Configure Your Git Identity

``` bash
git config user.name "Your Name"
git config user.email "your-email@example.com"
```

### Step 3: Get the Latest Code

For a normal contribution, start from `develop`:

``` bash
git fetch upstream
git checkout develop
git pull --ff-only upstream develop
```

If this project does not have a `develop` branch, use `main` instead.

---

## 4. Create Your Branch

Never work directly on `main` or `develop`.

Create a branch from the latest integration branch:

``` bash
git checkout develop
git pull --ff-only upstream develop
git checkout -b feature/my-feature
```

Examples:

``` bash
git checkout -b feature/add-profile-page
git checkout -b fix/fix-login-error
git checkout -b chore/update-installation-guide
git checkout -b chore/add-payment-tests
git checkout -b feature/auth-service-refactor
git checkout -b chore/update-node-version
```

### Naming convention

Use:

``` text
<type>/<short-description>
```

Use lowercase and hyphens.

Good:

``` text
feature/add-search
fix/fix-null-user
chore/api-documentation
```

Avoid:

``` text
mybranch
new-feature
changes
final
final2
test123
shourya-work
```

---

## 5. Make Your Changes

Before coding:

- Understand the issue/task completely.
- Check existing code before creating new files.
- Follow the project's existing architecture and naming conventions.
- Avoid modifying files unrelated to your task.
- Do not reformat entire files unless formatting is specifically part
  of your task.

### Keep changes small

Prefer:

``` text
1 feature → 1 branch → 1 focused PR
```

Instead of:

``` text
1 branch → feature + bug fix + README rewrite + dependency update
```

Small PRs are easier to review, merge, revert, and debug.

---

## 6. How to Minimize Merge Conflicts

Merge conflicts are usually caused by multiple people editing the same
lines/files or by branches becoming outdated.

Follow these rules.

### Rule 1: Sync before starting

Always start from the latest `develop`:

``` bash
git fetch upstream
git checkout develop
git pull --ff-only upstream develop
```

Then create your branch.

### Rule 2: Sync regularly

If your task takes several days:

``` bash
git fetch upstream
git checkout develop
git pull --ff-only upstream develop

git checkout feature/my-feature
git rebase develop
```

Resolve conflicts locally if they occur.

### Rule 3: Avoid unnecessary file changes

Do not:

- Reformat files unrelated to your task.
- Change indentation across an entire file.
- Rename unrelated variables.
- Modify unrelated configuration.
- Add unnecessary dependencies.
- Commit generated files unless the project requires them.

### Rule 4: Divide work by responsibility

If several contributors are working simultaneously, prefer separate
areas of ownership.

For example:

``` text
Contributor A → frontend/login
Contributor B → backend/auth
Contributor C → tests/auth
Contributor D → documentation
```

Avoid having multiple contributors edit the same large file at the same
time.

### Rule 5: Do not mix formatting with functionality

Bad:

``` text
feature/add-search
```

containing:

- Search implementation
- Entire codebase formatting
- Unrelated CSS cleanup
- Dependency upgrades

Better:

``` text
feature/add-search
chore/cleanup-api
chore/update-dependencies
```

### Rule 6: Use `git pull --ff-only`

Prefer:

``` bash
git pull --ff-only
```

This prevents Git from silently creating unnecessary merge commits in
your local branch.

---

## 7. Commit Guidelines

Make commits small and meaningful.

Good:

``` text
feat: add user search
fix: handle empty search query
test: add search controller tests
docs: update search API documentation
```

Avoid:

``` text
changes
updated stuff
final changes
fixed everything
asdf
```

### Recommended commit format

``` text
<type>: <short description>
```

Common types:

| Type | Use |
| --- | --- |
| `feat` | New functionality |
| `fix` | Bug fix |
| `docs` | Documentation |
| `test` | Tests |
| `refactor` | Internal restructuring |
| `chore` | Maintenance |
| `perf` | Performance improvement |
| `style` | Formatting/style-only change |

> Note: these commit-type prefixes (`feat`, `fix`, `docs`, `test`,
> `refactor`, `chore`, `perf`, `style`) describe the **commit**, and
> are more granular than the branch types in Section 1 on purpose —
> a single `chore/*` branch, for example, can contain both `docs:`
> and `test:` commits.

### Keep commits focused

Prefer:

``` text
feat: add registration endpoint
test: add registration tests
docs: document registration endpoint
```

over one huge commit containing everything.

---

## 8. Before Opening a Pull Request

Run the project's required checks.

Typical checks include:

``` bash
# Install dependencies
# Use the project's documented command

# Run tests
# Use the project's documented test command

# Run linter
# Use the project's documented lint command

# Build the project
# Use the project's documented build command
```

Then check your changes:

``` bash
git status
git diff
git log --oneline
```

Make sure:

- No secrets/API keys are committed.
- No passwords or credentials are committed.
- No unnecessary files are included.
- Tests pass.
- Your branch contains only relevant changes.
- Documentation is updated when necessary.

---

## 9. Rebase Before Opening/Updating a PR

Before requesting review, update your branch with the latest `develop`:

``` bash
git fetch upstream
git checkout develop
git pull --ff-only upstream develop

git checkout feature/my-feature
git rebase develop
```

If there are conflicts:

``` bash
git status
```

Resolve the conflicted files, then:

``` bash
git add <resolved-file>
git rebase --continue
```

Repeat until the rebase finishes.

If you need to cancel the rebase:

``` bash
git rebase --abort
```

After a rebase, if the branch was already pushed:

``` bash
git push --force-with-lease origin feature/my-feature
```

**Never use `git push --force` on shared branches.**

`--force-with-lease` is safer because it refuses to overwrite remote
work you do not know about.

---

## 10. Opening a Pull Request

Push your branch:

``` bash
git push -u origin feature/my-feature
```

Then open a Pull Request on GitHub.

For normal contributions:

``` text
your-branch → develop
```

For urgent production fixes:

``` text
fix-branch → main
```

### Your PR should contain

- A clear title.
- A short description of what changed.
- Why the change was necessary.
- Testing performed.
- Screenshots/videos for UI changes when useful.
- Related issue number, if applicable.
- Any known limitations.

### PR title examples

``` text
feat: add user profile page
fix: prevent duplicate payment requests
docs: improve installation instructions
test: add authentication test coverage
```

---

## 11. Pull Request Rules

Before requesting review:

- [ ] Branch is up to date with `develop`.
- [ ] Project builds successfully.
- [ ] Tests pass.
- [ ] No secrets are committed.
- [ ] No unrelated files were changed.
- [ ] PR has a clear title.
- [ ] PR description explains the change.
- [ ] Screenshots are included for important UI changes.
- [ ] Merge conflicts are resolved.
- [ ] Reviewer feedback has been addressed.

Do not repeatedly push unrelated changes to an existing PR. If the task
changes significantly, create a new branch/PR.

---

## 12. Handling Review Comments

Review comments are part of the contribution process.

If a reviewer requests changes:

1.  Understand the reason for the requested change.
2.  Make the change on the same branch.
3.  Run the tests again.
4.  Commit the change.
5.  Push the branch.
6.  Reply to the review comment when appropriate.

Do not create a new PR for every review comment unless a maintainer
specifically asks you to.

---

## 13. Keeping Your PR Conflict-Free

If your PR stays open for a long time, periodically update it.

Recommended:

``` bash
git fetch upstream
git checkout develop
git pull --ff-only upstream develop

git checkout feature/my-feature
git rebase develop

git push --force-with-lease
```

Do this especially when:

- `develop` has changed significantly.
- Someone modified the same area of the project.
- Your PR has been open for several days.
- GitHub reports merge conflicts.

---

## 14. Files You Should Be Careful With

Some files are more likely to cause conflicts.

Examples:

``` text
package.json
package-lock.json
yarn.lock
pnpm-lock.yaml
.env files
configuration files
database migrations
large shared components
routing files
global CSS files
```

If you need to modify one of these files, keep the change minimal and
communicate with other contributors when necessary.

### Never commit secrets

Never commit:

``` text
.env
API keys
private keys
passwords
database credentials
access tokens
```

Use an environment-variable example file such as:

``` text
.env.example
```

when the project requires configuration documentation.

---

## 15. Database Changes

If your contribution changes the database:

- Use the project's migration system.
- Never manually modify production data.
- Do not rewrite an already-applied migration unless the project
  explicitly permits it.
- Give migrations descriptive names.
- Test migrations both forward and, where supported, backward.
- Coordinate with maintainers if multiple contributors are creating
  migrations simultaneously.

Example:

``` text
migrations/
├── 001_create_users
├── 002_create_orders
└── 003_add_user_profile
```

---

## 16. Multiple Contributors Working on the Same Feature

When a feature is large, split it into smaller tasks.

Example:

``` text
feature/user-dashboard
│
├── feature/user-dashboard-ui
├── feature/user-dashboard-api
├── chore/user-dashboard-tests
└── chore/user-dashboard-docs
```

Each contributor should own a clearly defined part.

The feature owner or maintainer can then integrate the smaller PRs.

This is generally safer than having five contributors commit to one
shared branch.

---

## 17. Do Not Use Shared Personal Branches

Avoid branches such as:

``` text
shourya
rahul
frontend
backend
latest-work
testing
```

These branches become difficult to understand and frequently cause
conflicts.

Use task-specific branches instead:

``` text
feature/user-dashboard
fix/navbar-mobile
chore/user-auth-tests
chore/setup-guide
```

---

## 18. Emergency Hotfix Procedure

Use a `fix/*` branch created directly from `main` only for urgent
problems affecting the stable `main` branch.

``` bash
git fetch upstream
git checkout main
git pull --ff-only upstream main

git checkout -b fix/critical-login-error
```

Make the smallest possible fix.

Then:

``` bash
git add .
git commit -m "fix: resolve critical login error"
git push -u origin fix/critical-login-error
```

Open a PR targeting `main`.

After the fix is merged into `main`, make sure the same fix is also
present in `develop`.

---

## 19. If You Make a Mistake

Do not panic.

### Accidentally edited the wrong files

Before committing:

``` bash
git status
git restore <file>
```

### Accidentally committed locally

You can usually fix it before pushing:

``` bash
git reset --soft HEAD~1
```

### Accidentally pushed bad code

Do **not** immediately force-push or delete branches.

Tell a maintainer if the branch is shared or if the change affects
`main`/`develop`.

---

## 20. Golden Rules for New Contributors

If you remember nothing else, remember these:

1.  **Never push directly to `main`.**
2.  **Start every task from the latest `develop`.**
3.  **Create one branch per task.**
4.  **Keep your branch focused.**
5.  **Do not modify unrelated files.**
6.  **Commit small, logical changes.**
7.  **Pull/rebase from `develop` regularly for long-running work.**
8.  **Run tests before opening a PR.**
9.  **Never commit secrets.**
10. **Use `git push --force-with-lease`, not `git push --force`, after
    rebasing.**
11. **Keep PRs small and easy to review.**
12. **Ask before making large architectural changes.**

---

## 21. Quick Start for a New Contributor

If you are completely new to Git/GitHub, follow these commands.

``` bash
# 1. Clone your fork
git clone https://github.com/<your-username>/<repository-name>.git

# 2. Enter the project
cd <repository-name>

# 3. Add the original repository
git remote add upstream https://github.com/<organization-or-owner>/<repository-name>.git

# 4. Get the latest develop branch
git fetch upstream
git checkout develop
git pull --ff-only upstream develop

# 5. Create your task branch
git checkout -b feature/my-first-contribution

# 6. Make your changes

# 7. Check what changed
git status
git diff

# 8. Commit
git add <files-you-changed>
git commit -m "feat: describe my contribution"

# 9. Push your branch
git push -u origin feature/my-first-contribution

# 10. Open a Pull Request
# Target: develop
```

---

## 22. Contribution Philosophy

The goal is not to make the largest possible contribution. The goal is
to make a **clear, isolated, tested, and reviewable contribution**.

A good contribution should be:

``` text
Small
  ↓
Focused
  ↓
Tested
  ↓
Documented
  ↓
Easy to Review
  ↓
Easy to Merge
```

Following this workflow will significantly reduce merge conflicts and
make collaboration easier for everyone.

Thank you for contributing!
