# CI Pipeline

Every pull request to NiFi Hub runs automated quality checks before merging. Different checks fire depending on what files are modified.

---

## Bundle CI

**Workflow:** `bundle-ci.yml`
**Triggers:** PRs modifying `extensions/`, `pom.xml`, `checkstyle.xml`

When a PR touches extension bundle code, the workflow:

1. **Detects changed bundles** — walks the changed file list and identifies which bundle aggregator directories are affected
2. **Builds each changed bundle** in parallel with full quality checks:
   - **Checkstyle** — NiFi coding conventions enforced via `checkstyle.xml` (200-char lines, no star imports, `final` everywhere possible, SLF4J loggers, etc.)
   - **PMD** — static analysis rules aligned with Apache NiFi, defined in `pmd-ruleset.xml`
   - **Apache RAT** — verifies Apache 2.0 license headers are present on all source files
   - **Unit tests** — all tests run via Maven Surefire
   - **Code coverage** — minimum 80% line coverage enforced via JaCoCo; results uploaded to Codecov
3. **Posts a coverage summary** on the PR as a comment, showing line/branch/instruction percentages and a per-module breakdown

Only bundles whose source files changed are built — unaffected bundles are skipped.

## Flow CI

**Workflow:** `flow-ci.yml`
**Triggers:** PRs modifying `flows/`

When a PR touches flow definitions or flow tests, two jobs run in parallel:

### Flow Diff

Uses the [Snowflake Flow Diff Action](Introduction-and-Concepts--Snowflake-Flow-Diff-GitHub-Action) to post a human-readable summary of what changed in each modified flow, plus checkstyle violations. See that page for full details.

### Flow Validation Tests

1. **Detects changed flow buckets** — identifies which `flows/<bucket>/` directories are affected
2. **Runs pytest** against the corresponding `tests/` directory for each changed bucket
3. Tests validate flow structure (required components present, parameters defined, connections valid) using [nipyapi](https://github.com/Chaffelson/nipyapi)

## Code Compliance

**Workflow:** `code-compliance.yml`
**Triggers:** PRs and pushes to `main`

Runs security and compliance checks across the full codebase:

- **CodeQL** — GitHub's static analysis for security vulnerabilities (Java)
- **Checkstyle** — applied across all extension source files
- **PMD** — applied across all extension source files
- **Apache RAT** — license header verification

## Dependency Check

**Workflow:** `dependency-check.yml`
**Triggers:** PRs modifying `extensions/`

Verifies that all Maven dependencies in extension bundles are on their latest available versions. PRs that introduce outdated dependencies fail this check, keeping the dependency graph current.

## Required Checks

All PRs require at least **one approving review** plus all applicable CI checks passing before merging to `main`.
