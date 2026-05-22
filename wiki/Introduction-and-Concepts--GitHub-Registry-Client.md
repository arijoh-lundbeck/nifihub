# GitHub Registry Client

NiFi Hub uses a **GitHub Registry Client** so that flows stored in this repository can be versioned and imported into NiFi directly from Git — without a separate registry server. This page explains what that means in practice and what the full developer workflow looks like.

---

## What Is a NiFi Flow Registry Client?

NiFi has a built-in versioning system called the **Flow Registry**. When a registry client is configured, you can:

- **Version-control** a process group by committing it to the registry
- **Import** a versioned process group from the registry into any NiFi instance
- **Track drift** — NiFi shows when a running flow has diverged from its registered version
- **Roll back** to any previous version through the NiFi UI

Out of the box, NiFi ships with a Registry Client that connects to a dedicated NiFi Registry server. An alternative — and the approach used here — is a **GitHub Registry Client** that connects directly to a GitHub repository, using the repository itself as the registry store.

## Key Concepts

| Concept | Meaning |
|---------|---------|
| **Bucket** | A logical grouping of flows in the registry. In NiFi Hub this maps to a subdirectory under `flows/` (e.g., `examples`, `salesforce`). |
| **Flow** | A versioned flow definition representing a specific use case. Each `.json` file in a bucket is one flow. |
| **Version** | A snapshot of a flow at a point in time. With the GitHub Registry Client, versions correspond to Git commits. |
| **Branch** | The Git branch the registry client is working against. You can import flows from any branch and commit back to it. |

> **Note:** Datavolo discourages nested versioning — if Process Group A contains Process Group B, only one of them should be version-controlled in the registry at a time.

---

## Configuring the GitHub Registry Client in NiFi

To point a NiFi instance at this repository as a flow registry:

1. In NiFi, go to **Global Menu → Controller Settings → Registry Clients**
2. Add a new client of type **GitHub Registry Client**
3. Configure it with:
   - **Repository URL** — the GitHub repository URL
   - **Repository Owner** — the GitHub organisation or user
   - **Personal Access Token** — a GitHub PAT with `repository` read access (write access if you want to commit from NiFi)
4. Save — the `flows/` directory now appears as a browsable registry

---

## Versioning a Flow from NiFi

Once the registry client is configured, you can version any process group:

1. Build your flow on the NiFi canvas inside a Process Group
2. Right-click the Process Group → **Start Version Control**
3. Select the GitHub Registry Client, choose a bucket (maps to a `flows/<bucket>/` directory), and provide a flow name and initial commit message
4. NiFi commits the flow definition as a JSON file to the repository

From this point on, the process group displays a version badge in the NiFi UI showing its current version and whether it has drifted from the committed state.

---

## Developer Workflow: Feature Branch Development

The recommended approach mirrors standard software development practices using Git branches. A typical setup:

- `main` — represents flows that are deployed in production
- `dev` — integration branch for ongoing development
- `feature/<name>` — short-lived branches for individual changes

### Making a Change

1. **Create a feature branch** in GitHub from `main` (or `dev`): e.g., `feature/add-dedup-step`
2. In NiFi, open the Import from Registry toolbar and **import the flow from the feature branch** as a new Process Group
3. **Make your changes** inside the Process Group on the NiFi canvas — add or reconfigure processors, adjust connections, update parameters
4. **Commit from NiFi** — right-click the Process Group → **Commit Local Changes**, add a commit message. NiFi pushes the updated JSON to your feature branch in GitHub.
5. Repeat as needed — each commit is a new version in the registry

### Submitting for Review

1. In GitHub, **open a pull request** from your feature branch to `main`
2. The [Snowflake Flow Diff Action](Introduction-and-Concepts--Snowflake-Flow-Diff-GitHub-Action) runs automatically and posts a **human-readable summary of the flow changes** as a PR comment — reviewers see what processors changed, what connections were added or removed, what parameters changed, without reading raw JSON
3. Reviewers approve the PR
4. Merge to `main`

### Promoting to Production

After merging:

1. In NiFi, on the process group running the production version, click **Change Version** and select the latest version from the `main` branch
2. NiFi applies the update in place — running state is preserved where possible

---

## Managing Parameters Across Environments

Flow definitions should not contain hardcoded environment-specific values (connection strings, credentials, table names). NiFi **Parameters** solve this:

- Parameters are grouped into a **Parameter Context**, which has a one-to-one mapping with a Process Group
- **Parameter Context inheritance** lets you define shared parameters in a parent context and override specific values in child contexts — useful for promoting flows from dev to staging to production without modifying the flow definition itself
- **Parameter Providers** connect to external systems (secrets managers, configuration files) to populate Parameter Contexts — these are configured per-environment by admins and are not stored in the flow definition

When a flow is versioned in Git, its parameters are stored as names and (optionally) default values — the actual values are supplied by the Parameter Context in the runtime environment.

---

## Recommended SDLC Workflow

| Phase | Action |
|-------|--------|
| **Development** | Create a feature branch, import the flow from that branch in NiFi, make changes, commit from NiFi |
| **Code review** | Open a PR on GitHub; Flow Diff Action posts a readable diff; team reviews |
| **Integration** | Merge feature branch to `dev`; import from `dev` in the integration NiFi instance |
| **Release** | Merge `dev` to `main`; update production process groups to the latest `main` version |
| **Hotfix** | Branch from `main`, import flow, make targeted fix, commit, PR back to `main`, then cherry-pick or merge to `dev` |

For environment-specific configuration, use Parameter Contexts with different value sets per environment — never fork the flow definition itself.

---

## How NiFi Hub Uses This

Flows in `flows/<bucket>/` in this repository are the registry store. The `flows/examples/hello-world.json` file, for example, is a versioned flow definition that can be imported directly into NiFi using a GitHub Registry Client pointing at this repo, selecting the `examples` bucket.

Each flow has a companion `.md` file documenting its purpose and a `tests/` directory with structural validation tests. When a flow changes via PR, the CI pipeline runs both the [Snowflake Flow Diff Action](Introduction-and-Concepts--Snowflake-Flow-Diff-GitHub-Action) and the validation test suite automatically.
