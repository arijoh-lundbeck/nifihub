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

#!/usr/bin/env python3
"""Provision an ephemeral CI runtime from a test YAML configuration.

Creates network rules, EAI, runtime, waits for ACTIVE, then sets up
flow registries, controller services, and parameter providers.

Outputs the runtime URL to stdout for use by subsequent steps.

Usage:
    python scripts/ci/provision_ci_runtime.py \
        --config flows/data-generator/tests/test_postgres_cdc_demo.yaml \
        --runtime-name CI_POSTGRES_CDC_DEMO_114_12345
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cd"))

import yaml

from manage_deployment import snow_sql
from manage_eai import create_runtime_eai
from manage_runtime import create_runtime, describe_runtime
from manage_parameters import resolve_value
from setup_registry_client import setup as setup_registry
from manage_flows import configure_nifi
from manage_controller_services import reconcile_controller_services
from manage_parameter_providers import reconcile_parameter_providers


def get_conn():
    return {
        "account_url": os.environ["SNOWFLAKE_ACCOUNT_URL"],
        "pat": os.environ["SNOWFLAKE_PAT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "role": os.environ.get("SNOWFLAKE_ROLE", "OPENFLOW_ADMIN"),
    }


def get_runtime_url(database, schema, runtime_name, conn):
    rows = snow_sql(
        f"DESCRIBE OPENFLOW RUNTIME {database}.{schema}.{runtime_name}",
        **conn
    )
    if not rows:
        return ""
    row = rows[0] if isinstance(rows, list) else rows
    server_url = row.get("server_url") or row.get("SERVER_URL")
    if server_url:
        url = server_url.rstrip("/")
        if url.endswith("/nifi"):
            url = url[:-5] + "/nifi-api"
        else:
            url = url + "/nifi-api"
        return url
    return ""


def provision(config_path, runtime_name):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    conn = get_conn()
    deployment = config["deployment"]
    database = config["database"]
    schema = config["schema"]
    node_type = config.get("node_type", "MEDIUM")
    min_nodes = config.get("min_nodes", 1)
    max_nodes = config.get("max_nodes", 1)
    execute_as_role = config["execute_as_role"]
    network_rules = config.get("network_rules", [])

    print(f"[ci] Provisioning runtime {runtime_name} in {deployment}...", file=sys.stderr)

    eai = create_runtime_eai(
        runtime_name, network_rules,
        database, schema, execute_as_role=execute_as_role, **conn
    )

    create_runtime(
        runtime_name, deployment, database, schema,
        node_type, min_nodes, max_nodes,
        execute_as_role,
        eai_names=[eai],
        display_name=f"CI Runtime - {runtime_name}",
        comment=f"Ephemeral CI runtime for flow testing",
        **conn
    )

    runtime_url = get_runtime_url(database, schema, runtime_name, conn)
    if not runtime_url:
        raise RuntimeError(f"Could not get runtime URL for {runtime_name}")

    print(f"[ci] Runtime URL: {runtime_url}", file=sys.stderr)

    nifi_pat = os.environ["NIFI_RUNTIME_PAT"]
    configure_nifi(runtime_url, nifi_pat)

    for rc in config.get("flow_registries", []):
        properties = {k: resolve_value(v) for k, v in rc.get("properties", {}).items()}
        setup_registry(
            rc["name"], properties, runtime_url, nifi_pat,
            type_override=rc.get("type"),
        )

    services = config.get("controller_services", [])
    if services:
        reconcile_controller_services(services, runtime_url, nifi_pat)

    providers = config.get("parameter_providers", [])
    if providers:
        reconcile_parameter_providers(providers, runtime_url, nifi_pat)

    print(runtime_url)
    return runtime_url


def main():
    parser = argparse.ArgumentParser(description="Provision an ephemeral CI runtime")
    parser.add_argument("--config", required=True, help="Path to test YAML configuration")
    parser.add_argument("--runtime-name", required=True, help="Name for the ephemeral runtime")
    parser.add_argument("--output-file", help="File to write runtime URL to (instead of stdout)")
    args = parser.parse_args()

    try:
        url = provision(args.config, args.runtime_name)
        if args.output_file:
            with open(args.output_file, "w") as f:
                f.write(url)
    except Exception as exc:
        print(f"[ci] Provisioning failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()