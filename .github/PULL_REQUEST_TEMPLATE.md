## Description

<!-- Describe your changes. What does this PR add, change, or fix? -->

## Type of Change

- [ ] New extension bundle
- [ ] Extension bundle update
- [ ] New flow definition
- [ ] Flow definition update
- [ ] Infrastructure / CI change
- [ ] Documentation

## Checklist

### For Extension Bundles
- [ ] Build passes: `./mvnw clean verify -Pcontrib-check -f <bundle-path>/pom.xml`
- [ ] Unit tests added/updated
- [ ] Code coverage >= 80%
- [ ] `SKILL.md` added/updated at bundle root
- [ ] Apache 2.0 license header on all new files
- [ ] All code in package `com.snowflake.nifihub.*`

### For Flow Definitions
- [ ] Flow JSON is valid and exported from NiFi
- [ ] Companion `.md` documentation added/updated
- [ ] Validation tests added at `flows/<bucket>/tests/`
- [ ] Tests pass: `pytest flows/<bucket>/tests/ -v`

### General
- [ ] No secrets or credentials in the PR
- [ ] Documentation is clear and complete
