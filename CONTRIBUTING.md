# Contributing to NiFi Hub

> **Disclaimer:** The contents of this repository are community-driven and provided on an "AS IS" basis, without warranties of any kind, express or implied. They are NOT supported by Snowflake and do not constitute a Snowflake product or service. Snowflake makes no guarantees regarding functionality, compatibility, availability, or fitness for any particular purpose, and assumes no liability arising from use of this repository. Community support is available through GitHub Issues and Pull Requests.

Thank you for your interest in contributing to NiFi Hub! This document explains how to contribute extension bundles and flow definitions.

## Prerequisites

- Java 21 or later
- Maven 3.9+ (or use the included `./mvnw` wrapper)
- Python 3.12+ (for flow tests)
- Git

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch: `git checkout -b my-new-bundle`
4. Make your changes
5. Push and open a Pull Request

## Contributing an Extension Bundle

### Directory Structure

Create your bundle under `extensions/<category>/<sub-category>/nifi-<name>-bundle/`:

```
nifi-<name>-bundle/
├── pom.xml                          # Aggregator POM (packaging: pom)
├── SKILL.md                         # Agent-readable documentation
├── nifi-<name>-processors/
│   ├── pom.xml                      # Processor jar (packaging: jar)
│   └── src/
│       ├── main/java/com/snowflake/nifihub/<category>/<name>/
│       ├── main/resources/META-INF/services/org.apache.nifi.processor.Processor
│       └── test/java/com/snowflake/nifihub/<category>/<name>/
└── nifi-<name>-nar/
    └── pom.xml                      # NAR archive (packaging: nar)
```

### Requirements

- [ ] Bundle POM references `nifihub-parent` as parent via `<relativePath>`
- [ ] All Java code is in package `com.snowflake.nifihub.<category>.<name>`
- [ ] Apache 2.0 license header on all source files
- [ ] Unit tests using `nifi-mock` framework
- [ ] Code coverage >= 80%
- [ ] `SKILL.md` documenting the bundle's purpose, processors, and usage
- [ ] Build passes: `./mvnw clean verify -Pcontrib-check -f <bundle-path>/pom.xml`

### Code Style

This project follows Apache NiFi coding conventions:

- All variables that can be `final` must be `final`
- No star imports
- No underscores in class names, variables, or filenames
- 200 character line width maximum
- 4-space indentation
- Use SLF4J loggers (never `System.out.println`)
- Use `.formatted()` for string formatting

Use the provided `checkstyle.xml` and `pmd-ruleset.xml` to validate your code automatically via `-Pcontrib-check`.

## Contributing a Flow Definition

### Directory Structure

Place your flow under `flows/<bucket>/`:

```
flows/<bucket>/
├── <flow-name>.json    # NiFi flow definition (exported JSON)
├── <flow-name>.md      # Documentation explaining the flow
└── tests/
    └── test_<flow-name>.py  # Validation tests
```

### Requirements

- [ ] Flow exported as valid JSON from NiFi
- [ ] Companion `.md` file explaining purpose, parameters, required NARs, and configuration
- [ ] Validation tests in `flows/<bucket>/tests/test_<flow-name>.py`
- [ ] Tests pass: `pytest flows/<bucket>/tests/ -v`

## Pull Request Checklist

Before submitting your PR, ensure:

- [ ] Branch is up to date with `main`
- [ ] For bundles: `./mvnw clean verify -Pcontrib-check` passes
- [ ] For bundles: Code coverage >= 80%
- [ ] For flows: `pytest` tests pass
- [ ] `SKILL.md` or flow `.md` documentation is included
- [ ] License headers are present on all new files
- [ ] No secrets, credentials, or sensitive data in the PR

## CI/CD

All PRs are automatically checked:

- **Bundle PRs**: Checkstyle, PMD, RAT, unit tests, code coverage (Codecov)
- **Flow PRs**: Snowflake Flow Diff (comments on the PR), nipyapi validation tests, flow checkstyle
- **All PRs**: Require at least one approving review

## Releases

To release a bundle, change the `<revision>` property in its aggregator `pom.xml` from `X.Y.Z-SNAPSHOT` to `X.Y.Z` and merge the PR. The **Auto Release** workflow will automatically build the bundle, create a GitHub Release with the NAR attached, and bump the version to the next patch SNAPSHOT.

For manual releases (version jumps, retries), admins can use the **Release Bundle** workflow from the Actions tab.

## Branch Protection

The `main` branch requires:

- At least 1 approving review
- All CI checks passing
- No force pushes

## Questions?

Open an issue or reach out to the maintainers listed in `CODEOWNERS`.
