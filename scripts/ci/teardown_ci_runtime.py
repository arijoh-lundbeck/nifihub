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
"""Tear down an ephemeral CI runtime.

Stops all flows, suspends, terminates, and drops the runtime plus
its EAI and network rules.

Usage:
    python scripts/ci/teardown_ci_runtime.py \
        --config flows/data-generator/tests/test_postgres_cdc_demo.yaml \
        --runtime-name CI_POSTGRES_CDC_DEMO_114_12345
"""
import argparse
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cd"))

import yaml

from manage_deployment import snow_sql
from manage_eai import delete_runtime_eai
from manage_runtime import delete_runtime, describe_runtime
from manage_flows import configure_nifi, list_process_groups, stop_flow


def get_conn():
    return {
        "account_url": os.environ["SNOWFLAKE_ACCOUNT_URL"],
        "pat": os.environ["SNOWFLAKE_PAT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "role": os.environ.get("SNOWFLAKE_ROLE", "OPENFLOW_ADMIN"),
    }


def get_runtime_url(database, schema, runtime_name, conn):
    try:
        rows = snow_sql(
            f"DESCRIBE OPENFLOW RUNTIME {database}.{schema}.{runtime_name}",
            **conn
        )
    except Exception:
        return ""
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


def stop_all_flows(runtime_url, nifi_pat):
    try:
        configure_nifi(runtime_url, nifi_pat)
        pgs = list_process_groups()
        for pg in pgs:
            try:
                stop_flow(pg.id, pg.component.name)
            except Exception as e:
                print(f"[ci] Could not stop PG '{pg.component.name}': {e}", file=sys.stderr)
    except Exception as e:
        print(f"[ci] Could not list/stop flows: {e}", file=sys.stderr)


def teardown(config_path, runtime_name):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    conn = get_conn()
    database = config["database"]
    schema = config["schema"]
    network_rules = config.get("network_rules", [])

    print(f"[ci] Tearing down runtime {runtime_name}...", file=sys.stderr)

    runtime_url = get_runtime_url(database, schema, runtime_name, conn)
    if runtime_url:
        nifi_pat = os.environ.get("NIFI_RUNTIME_PAT", "")
        if nifi_pat:
            stop_all_flows(runtime_url, nifi_pat)

    try:
        delete_runtime(runtime_name, database, schema, **conn)
    except Exception as e:
        print(f"[ci] Runtime delete failed: {e}", file=sys.stderr)
        traceback.print_exc()

    try:
        delete_runtime_eai(
            runtime_name, network_rules,
            database=database, schema=schema, **conn
        )
    except Exception as e:
        print(f"[ci] EAI cleanup failed: {e}", file=sys.stderr)

    print(f"[ci] Teardown complete for {runtime_name}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Tear down an ephemeral CI runtime")
    parser.add_argument("--config", required=True, help="Path to test YAML configuration")
    parser.add_argument("--runtime-name", required=True, help="Name of the runtime to tear down")
    args = parser.parse_args()

    try:
        teardown(args.config, args.runtime_name)
    except Exception as exc:
        print(f"[ci] Teardown failed: {exc}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()