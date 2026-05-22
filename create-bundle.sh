#!/usr/bin/env bash
#
# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Scaffolds a new NiFi Hub extension bundle.
#
# Usage: ./create-bundle.sh <category> <sub-category> <bundle-name>
# Example: ./create-bundle.sh data snowflake nifi-snowflake-ingest

set -euo pipefail

if [ $# -ne 3 ]; then
  echo "Usage: $0 <category> <sub-category> <bundle-name>"
  echo "Example: $0 data snowflake nifi-snowflake-ingest"
  exit 1
fi

CATEGORY="$1"
SUB_CATEGORY="$2"
BUNDLE_NAME="$3"

# Derive names
if [[ "$BUNDLE_NAME" != *-bundle ]]; then
  BUNDLE_NAME="${BUNDLE_NAME}-bundle"
fi

BASE_NAME="${BUNDLE_NAME%-bundle}"
PROCESSORS_NAME="${BASE_NAME}-processors"
NAR_NAME="${BASE_NAME}-nar"

# Derive package path from category and short name (strip nifi- prefix)
SHORT_NAME="${BASE_NAME#nifi-}"
PACKAGE_NAME="com.snowflake.nifihub.${CATEGORY}.${SHORT_NAME//-/}"
PACKAGE_PATH="${PACKAGE_NAME//./\/}"

BUNDLE_DIR="extensions/${CATEGORY}/${SUB_CATEGORY}/${BUNDLE_NAME}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Calculate relative path back to root pom.xml
REL_PATH=$(python3 -c "import os.path; print(os.path.relpath('${SCRIPT_DIR}', '${SCRIPT_DIR}/${BUNDLE_DIR}'))")

LICENSE_HEADER='<!--
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->'

JAVA_LICENSE='/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */'

echo "Creating bundle: ${BUNDLE_DIR}"

# Create directories
mkdir -p "${BUNDLE_DIR}/${PROCESSORS_NAME}/src/main/java/${PACKAGE_PATH}"
mkdir -p "${BUNDLE_DIR}/${PROCESSORS_NAME}/src/main/resources/META-INF/services"
mkdir -p "${BUNDLE_DIR}/${PROCESSORS_NAME}/src/test/java/${PACKAGE_PATH}"
mkdir -p "${BUNDLE_DIR}/${NAR_NAME}"

# Bundle POM
cat > "${BUNDLE_DIR}/pom.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
${LICENSE_HEADER}
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>com.snowflake.nifihub</groupId>
        <artifactId>nifihub-parent</artifactId>
        <version>1</version>
        <relativePath>${REL_PATH}/pom.xml</relativePath>
    </parent>

    <artifactId>${BUNDLE_NAME}</artifactId>
    <version>\${revision}</version>
    <packaging>pom</packaging>

    <name>${BUNDLE_NAME}</name>

    <properties>
        <revision>0.1.0-SNAPSHOT</revision>
    </properties>

    <modules>
        <module>${PROCESSORS_NAME}</module>
        <module>${NAR_NAME}</module>
    </modules>

    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>com.snowflake.nifihub</groupId>
                <artifactId>${PROCESSORS_NAME}</artifactId>
                <version>\${revision}</version>
            </dependency>
        </dependencies>
    </dependencyManagement>
</project>
EOF

# Processors POM
cat > "${BUNDLE_DIR}/${PROCESSORS_NAME}/pom.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
${LICENSE_HEADER}
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>com.snowflake.nifihub</groupId>
        <artifactId>${BUNDLE_NAME}</artifactId>
        <version>\${revision}</version>
    </parent>

    <artifactId>${PROCESSORS_NAME}</artifactId>
    <packaging>jar</packaging>

    <dependencies>
        <dependency>
            <groupId>org.apache.nifi</groupId>
            <artifactId>nifi-api</artifactId>
        </dependency>
        <dependency>
            <groupId>org.apache.nifi</groupId>
            <artifactId>nifi-utils</artifactId>
        </dependency>
        <dependency>
            <groupId>org.apache.nifi</groupId>
            <artifactId>nifi-mock</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-api</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter-engine</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-simple</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
EOF

# NAR POM
cat > "${BUNDLE_DIR}/${NAR_NAME}/pom.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
${LICENSE_HEADER}
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>com.snowflake.nifihub</groupId>
        <artifactId>${BUNDLE_NAME}</artifactId>
        <version>\${revision}</version>
    </parent>

    <artifactId>${NAR_NAME}</artifactId>
    <packaging>nar</packaging>

    <dependencies>
        <dependency>
            <groupId>com.snowflake.nifihub</groupId>
            <artifactId>${PROCESSORS_NAME}</artifactId>
        </dependency>
    </dependencies>
</project>
EOF

# Service registration (empty, to be filled)
cat > "${BUNDLE_DIR}/${PROCESSORS_NAME}/src/main/resources/META-INF/services/org.apache.nifi.processor.Processor" << 'EOF'
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
EOF

# SKILL.md
cat > "${BUNDLE_DIR}/SKILL.md" << EOF
# ${BUNDLE_NAME}

## Purpose

<!-- Describe what this bundle does -->

## Processors

<!-- List and describe each processor -->

## Building

\`\`\`bash
./mvnw clean verify -Pcontrib-check -f ${BUNDLE_DIR}/pom.xml
\`\`\`

## Testing

\`\`\`bash
./mvnw test -f ${BUNDLE_DIR}/pom.xml
\`\`\`
EOF

echo "Bundle scaffolded at: ${BUNDLE_DIR}"
echo ""
echo "Next steps:"
echo "  1. Add processor classes to ${BUNDLE_DIR}/${PROCESSORS_NAME}/src/main/java/${PACKAGE_PATH}/"
echo "  2. Register processors in META-INF/services/org.apache.nifi.processor.Processor"
echo "  3. Add unit tests to ${BUNDLE_DIR}/${PROCESSORS_NAME}/src/test/java/${PACKAGE_PATH}/"
echo "  4. Update SKILL.md with bundle documentation"
echo "  5. Build: ./mvnw clean verify -Pcontrib-check -f ${BUNDLE_DIR}/pom.xml"
