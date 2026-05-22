# Hello World Flow

**Bucket:** `examples`
**File:** [`flows/examples/hello-world.json`](../flows/examples/hello-world.json)

A minimal example flow demonstrating the NiFi Hub flow structure. It generates a FlowFile with a static message and logs its attributes every 5 seconds.

---

## Purpose

This flow exists as a reference implementation showing how flows in NiFi Hub are structured — the JSON definition, companion documentation, and validation tests. It is not intended for production use.

## Components

| Component | Type | Description |
|-----------|------|-------------|
| GenerateFlowFile | Processor | Generates a FlowFile every 5 seconds with the content `Hello, NiFi Hub!` |
| LogAttribute | Processor | Logs all attributes and the payload of each incoming FlowFile at INFO level |

## Required NARs

- `org.apache.nifi:nifi-standard-nar:2.8.0` — included with standard NiFi installations, no additional download required

## Parameters

This flow does not use any parameters.

## Configuration

No additional configuration is required. Import the flow definition into NiFi and start the process group.

## Expected Behaviour

Once started, the flow produces a log entry every 5 seconds containing the FlowFile attributes and the `Hello, NiFi Hub!` content. Output is visible in the NiFi log file and in the Data Provenance view.

## Validation Tests

The test file at [`flows/examples/tests/test_hello_world.py`](../flows/examples/tests/test_hello_world.py) validates:

- The flow imports successfully as a process group
- Both processors (GenerateFlowFile and LogAttribute) are present
- The connection between them exists
