# NiFi Example Bundle

## Purpose

This is a starter example bundle that demonstrates the standard NiFi Hub bundle structure. It serves as a template for contributors creating new extension bundles.

## Processors

### ExampleProcessor

Adds a configurable attribute to each incoming FlowFile.

**Properties:**
- **Attribute Name** (required): The name of the attribute to add
- **Attribute Value** (required, supports Expression Language): The value of the attribute to add

**Relationships:**
- **success**: All successfully processed FlowFiles

**Usage Example:**
Configure the processor with `Attribute Name = "environment"` and `Attribute Value = "production"` to stamp every FlowFile with an environment attribute.

## Building

```bash
mvn clean verify -f extensions/examples/getting-started/nifi-example-bundle/pom.xml
```

With checkstyle and PMD:

```bash
mvn clean verify -Pcontrib-check -f extensions/examples/getting-started/nifi-example-bundle/pom.xml
```

## Testing

Unit tests use the `nifi-mock` framework via `TestRunner`. Run tests with:

```bash
mvn test -f extensions/examples/getting-started/nifi-example-bundle/pom.xml
```

## Bundle Structure

```
nifi-example-bundle/
├── pom.xml                      # Aggregator POM (packaging: pom)
├── SKILL.md                     # This file
├── nifi-example-processors/     # Processor implementations (packaging: jar)
│   ├── pom.xml
│   └── src/
│       ├── main/java/...        # Processor source code
│       ├── main/resources/...   # Service registration
│       └── test/java/...        # Unit tests
└── nifi-example-nar/            # NAR archive (packaging: nar)
    └── pom.xml
```
