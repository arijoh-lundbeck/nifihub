# Snowflake Flow Diff GitHub Action

NiFi flow definitions are large JSON files. A raw JSON diff of a flow change is unreadable — processor names, connection topology, and configuration are buried in deeply nested structures. The **Snowflake Flow Diff** Action solves this by parsing both versions of a flow and posting a structured, human-readable summary directly in the pull request conversation.

Every PR that modifies a flow JSON file in this repository triggers this action automatically as part of the [Flow CI](Introduction-and-Concepts--CI) workflow.

---

## Why It Matters

Without Flow Diff, reviewing a flow change in a PR looks like this — two large JSON blobs with structural differences scattered throughout. With Flow Diff, reviewers see exactly what changed at the semantic level:

```
### Executing Snowflake Flow Diff for flow: `MyExample`

#### Flow Changes
- The destination of a connection has changed from `UpdateAttribute` to `InvokeHTTP`
- A self-loop connection `[success]` has been added on `UpdateAttribute`
- A Processor of type `GenerateFlowFile` named `GenerateFlowFile` has been renamed to `My Generate FlowFile Processor`
- In Processor of type `GenerateFlowFile`, the Scheduling Strategy changed from `TIMER_DRIVEN` to `CRON_DRIVEN`
- A Parameter Context named `Test Parameter Context` has been added
- A Processor of type `UpdateAttribute` named `UpdateAttribute` has been removed
- A Processor of type `UpdateAttribute` named `UpdateAttribute` has been added with the configuration
  [`ALL` nodes, `4` concurrent tasks, `0ms` run duration, `WARN` bulletin level,
   `TIMER_DRIVEN` (`0 sec`), `30 sec` penalty duration, `1 sec` yield duration]

#### Bundle Changes
- The bundle `org.apache.nifi:nifi-standard-nar` has been changed from version `2.1.0` to version `2.2.0`
```

This gives reviewers a precise, reviewable description of the change without needing to import the flow into NiFi.

---

## Checkstyle for Flows

In addition to the diff, the action can run **flow checkstyle rules** — best-practice checks that catch common configuration issues before they reach production. When violations are found, they appear as a caution block above the diff in the PR comment:

```
#### Checkstyle Violations
> [!CAUTION]
> - Processor named `UpdateAttribute` is configured with 4 concurrent tasks
```

### Rules Configured in This Repo

The rules are defined in `.github/checkstyle/flow-checkstyle-rules.yaml`:

| Rule | What it checks | Configured limit |
|------|---------------|-----------------|
| `concurrentTasks` | Processors should not exceed N concurrent tasks | 4 |
| `snapshotMetadata` | Flow snapshot metadata must be present in the file | — |
| `emptyParameter` | No parameter should be set to an empty string | — |
| `unusedParameter` | All defined parameters must be referenced in the flow | — |
| `noSelfLoop` | Processors must not have relationships that loop back to themselves | — |
| `backpressureThreshold` | All connections must have object count and data size backpressure thresholds greater than zero | — |

### All Available Rules

The full set of rules the action supports:

| Rule | Description |
|------|-------------|
| `concurrentTasks` | Upper limit on concurrent tasks per processor (default: 2; configurable) |
| `snapshotMetadata` | Flow snapshot metadata must be present |
| `emptyParameter` | Parameters must not be set to empty strings |
| `defaultParameters` | Checks for parameters with expected default values |
| `unusedParameter` | Parameters defined but never referenced in the flow |
| `noSelfLoop` | No self-loop connections on processors |
| `enforcePrioritizer` | All connections must use a specified prioritizer |
| `backpressureThreshold` | Connections must have non-zero backpressure thresholds on both object count and data size |

### Rule Configuration

Rules are configured in a YAML file:

```yaml
include:
  - concurrentTasks
  - noSelfLoop
  - backpressureThreshold

rules:
  concurrentTasks:
    parameters:
      limit: 4
    overrides:
      ".*sql-connector":   # regex against flow name — applies a different limit
        limit: 8
    exclude:
      - "LegacyFlow.*"     # regex — skip this rule entirely for matching flows
    componentExclusions:
      "ProductionFlow.*":
        - "1a59f65f-8b3a-3db9-982e-e0d334bd7e9c"   # suppress for specific processor UUID
```

- **`include`** — if specified, only these rules run (others are skipped)
- **`exclude`** — if specified without `include`, all rules except these run
- **`overrides`** — per-flow parameter overrides, matched by flow name regex
- **`componentExclusions`** — suppress a violation for a specific processor or connection UUID within matching flows (useful for one-off exceptions without disabling the rule globally)

Setting `checkstyle-fail: true` in the action step causes the workflow to fail if any violations are detected, blocking the PR until they are resolved.

---

## How the Action Is Integrated Here

The action runs inside the `flow-diff` job of `.github/workflows/flow-ci.yml`. When a PR touches a file under `flows/`, the workflow:

1. Checks out both the PR branch and the base branch
2. Identifies changed `.json` files
3. Runs the action with `checkstyle: true` and the rules file above
4. Posts the diff and any violations as a PR comment

The action is pinned at `Snowflake-Labs/snowflake-flow-diff@v0`.

---

## Setting Up the Action in Your Own Repo

If you fork this repository or use a separate repository for flow versioning, add this workflow file:

```yaml
# .github/workflows/flowdiff.yml
name: Snowflake Flow Diff on Pull Requests

on:
  pull_request:
    types: [opened, reopened, synchronize]

jobs:
  execute_flow_diff:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    name: Executing Flow Diff
    steps:
      - name: Checkout PR code
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.ref }}
          fetch-depth: 0
          path: submitted-changes

      - name: Get changed files
        id: files
        run: |
          cd submitted-changes
          files=$(git diff --name-only \
            $(git merge-base HEAD origin/${{ github.event.pull_request.base.ref }}) \
            HEAD | grep 'flows/.*\.json$')
          bare=$(echo "$files" | tr '\n' ',' | sed 's/,$//')
          echo "flowA=$(echo "$bare" | sed 's|[^,]\+|original-code/&|g')" >> $GITHUB_OUTPUT
          echo "flowB=$(echo "$bare" | sed 's|[^,]\+|submitted-changes/&|g')" >> $GITHUB_OUTPUT

      - name: Checkout original code
        uses: actions/checkout@v4
        with:
          fetch-depth: 2
          path: original-code
      - run: cd original-code && git checkout HEAD^

      - name: Snowflake Flow Diff
        uses: snowflake-labs/snowflake-flow-diff@v0
        with:
          flowA: ${{ steps.files.outputs.flowA }}
          flowB: ${{ steps.files.outputs.flowB }}
          checkstyle: true
          checkstyle-rules: submitted-changes/.github/checkstyle/flow-checkstyle-rules.yaml
```

The action works with both GitHub.com and GitHub Enterprise Server — the API URL is detected automatically.

---

## Source

The action is published at [Snowflake-Labs/snowflake-flow-diff](https://github.com/Snowflake-Labs/snowflake-flow-diff).
