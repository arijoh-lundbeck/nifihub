# How to Contribute

Contributions to NiFi Hub are welcome — whether adding a new extension bundle, a new flow, or improving existing ones. This page summarises the process; see [CONTRIBUTING.md](../CONTRIBUTING.md) in the repository root for complete requirements.

---

## Prerequisites

- Java 21+ (Maven is provided via `./mvnw` wrapper)
- Python 3.12+ (for flow validation tests)
- Git

---

## Contributing an Extension Bundle

### 1. Scaffold the Bundle

Use the provided script to generate the standard directory structure:

```bash
./create-bundle.sh <category> <sub-category> <name>
# Example: ./create-bundle.sh data snowflake nifi-snowflake
```

This creates `extensions/<category>/<sub-category>/nifi-<name>-bundle/` with the correct POM hierarchy, package structure, and a starter processor.

Alternatively, copy the [example bundle](../extensions/examples/getting-started/nifi-example-bundle/) as a template and rename.

### 2. Implement the Processor

- Place Java source in `nifi-<name>-processors/src/main/java/com/snowflake/nifihub/<category>/<name>/`
- Register the processor in `src/main/resources/META-INF/services/org.apache.nifi.processor.Processor`
- Write unit tests using the `nifi-mock` framework (minimum 80% line coverage required)

### 3. Follow Code Style

This project uses NiFi's coding conventions:

- All variables that can be `final` must be `final`
- No star imports
- 200-character line width maximum, 4-space indentation
- SLF4J loggers (never `System.out.println`)
- Apache 2.0 license header on all source files

Run the full check locally before opening a PR:

```bash
./mvnw clean verify -Pcontrib-check -f extensions/<your-bundle>/pom.xml
```

### 4. Write a SKILL.md

Each bundle needs a `SKILL.md` at its root documenting its purpose, processors, configuration, and usage examples. This file is used by AI coding assistants to understand the bundle.

### 5. Open a Pull Request

- The [Bundle CI](Introduction-and-Concepts--CI) workflow will run automatically
- Coverage results are posted as a PR comment
- At least one approving review is required

---

## Contributing a Flow Definition

### 1. Export the Flow from NiFi

In the NiFi UI, right-click the process group you want to share and select **Download Flow Definition** (NiFi 2.x) or **Download Flow** (NiFi 1.x). Save the JSON file.

### 2. Place Files in the Repo

```
flows/<bucket>/
├── <flow-name>.json    # The exported flow definition
├── <flow-name>.md      # Documentation (see below)
└── tests/
    └── test_<flow-name>.py  # Validation tests
```

Choose or create a `<bucket>` that matches the flow's category (e.g., `examples`, `salesforce`, `data`).

### 3. Write the Documentation

The `.md` file must explain:
- **Purpose** — what the flow does
- **Components** — key processors and controller services
- **Required NARs** — which NAR files must be installed
- **Parameters** — any NiFi parameters the flow uses
- **Configuration** — how to set it up after import
- **Expected Behaviour** — what the flow does when running

See [hello-world.md](../flows/examples/hello-world.md) as an example.

### 4. Write Validation Tests

Tests in `tests/test_<flow-name>.py` use `nipyapi` to validate the flow's structure without running it. Typical checks:

- Process group imports successfully
- Required processors are present and of the right type
- Required controller services are present
- Parameters are defined
- Connections are correctly wired

Run tests locally:

```bash
pip install -r flows/requirements.txt
pytest flows/<bucket>/tests/ -v
```

### 5. Open a Pull Request

- The [Flow CI](Introduction-and-Concepts--CI) workflow runs the Snowflake Flow Diff Action and validation tests automatically
- The flow diff and any checkstyle violations are posted as a PR comment
- At least one approving review is required
- Maintainers can optionally trigger a live deploy test with `deploy this flow` — see [CD Pipeline](Introduction-and-Concepts--CD)

---

## Releasing a Bundle

To publish a new version of a bundle:

1. In a PR, change the `<revision>` property in the bundle's `pom.xml` from `X.Y.Z-SNAPSHOT` to `X.Y.Z`
2. Merge the PR to `main`
3. The **Auto Release** workflow detects the non-SNAPSHOT version and automatically builds the bundle, creates a GitHub Release with the NAR attached, and bumps the version to `X.Y.(Z+1)-SNAPSHOT`

For version jumps or retries, admins can use the **Release Bundle** workflow from the Actions tab.

---

## Questions?

Open an issue or reach out to the maintainers listed in [CODEOWNERS](../.github/CODEOWNERS).
