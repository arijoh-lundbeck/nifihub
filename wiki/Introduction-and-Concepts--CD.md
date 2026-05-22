# CD Pipeline

NiFi Hub has two CD mechanisms: **Flow Deploy** for testing flows against a live Snowflake runtime during PR review, and **Environment CD** for managing Openflow infrastructure declaratively as code.

---

## Flow Deploy

**Workflow:** `flow-deploy.yml`
**Trigger:** A maintainer with admin or maintain permission comments `deploy this flow` on a PR

This workflow lets maintainers test a flow against a real Snowflake Openflow runtime before merging. It is intended as a validation step during PR review, not for production deployment.

### What Happens

1. The workflow identifies flow JSON files changed in the PR
2. **Builds all extension bundles** and uploads the resulting NARs to the target runtime
3. **Deploys each changed flow** as a process group on the runtime, using the runtime's REST API
4. **Runs the flow's validation tests** (`flows/<bucket>/tests/test_<flow-name>.py`) against the deployed process group
5. **Cleans up** the deployed process group and uploaded NARs (unless the comment includes "do not clean")
6. **Posts a comment** on the PR with deployment details, processor/controller service summary, and per-test results

### Configuration

The target runtime is configured via a GitHub Environment named `snowflake-runtime-ci`, which provides:
- `SNOWFLAKE_RUNTIME_URL` — the Openflow runtime endpoint
- `SNOWFLAKE_RUNTIME_PAT` — a PAT with permission to deploy to the runtime

---

## Environment CD

**Workflows:** `environment-cd.yml` (apply) and `environment-cd-validate.yml` (PR validation)
**Triggers:** Changes to `environments/**/config.yaml`

NiFi Hub uses a **GitOps** model for managing Openflow infrastructure. The `environments/` directory contains one subdirectory per environment, each with a `config.yaml` that declaratively describes the desired state of that environment's Openflow resources.

### What Gets Managed

| Resource | Operation |
|---|---|
| Openflow Deployments | Created, altered, or terminated via Snowflake SQL |
| Network Rules & EAIs | Created automatically from YAML entries to allow runtime egress access |
| Openflow Runtimes | Created with EAI bindings; polled until ACTIVE |
| Flow Registry Clients | Git-based clients configured via NiFi REST API |
| Imported Flows | Pulled from the Git registry at a specified version |

### PR Validation

When a PR modifies an environment config, the **Environment CD Validate** workflow:

1. Computes the diff between the current and proposed config
2. Validates the proposed config against the [JSON schema](../environments/schema.json)
3. Runs connectivity checks against the target Snowflake account
4. Posts a **change plan** comment on the PR showing exactly what resources will be created, modified, or deleted

This gives reviewers a clear picture of the infrastructure impact before merging.

### Applying Changes

When the PR merges to `main`, the **Environment CD** workflow applies the change plan to the target Snowflake account. Each environment runs in a separate GitHub Environment with its own credentials (`SNOWFLAKE_ACCOUNT_URL`, `SNOWFLAKE_USER`, `SNOWFLAKE_PAT`, `SNOWFLAKE_ROLE`).

### Forking for Your Own Environment

1. Fork this repository
2. Create `environments/<your-env>/config.yaml` following the [schema](../environments/README.md)
3. Set up a GitHub Environment named `<your-env>` with your Snowflake credentials
4. Open a PR — the validate workflow will show you the change plan
5. Merge to `main` — your infrastructure is provisioned automatically
