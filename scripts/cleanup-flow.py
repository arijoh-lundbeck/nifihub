#!/usr/bin/env python3
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
"""
Clean up a deployed NiFi process group from a Snowflake runtime.

Sequence: stop PG -> disable controller services -> purge queues -> delete PG.

Usage:
    python scripts/cleanup-flow.py --pg-id <uuid> \
        --runtime-url https://host.snowflakecomputing.app/instance-name --pat <token>
"""

import argparse
import re
import sys

import nipyapi


def cleanup(pg_id, runtime_url, pat):
    """Remove a deployed process group from the runtime."""
    base = re.sub(r"/nifi/?$", "", runtime_url.rstrip("/"))
    api_base = base + "/nifi-api"
    nipyapi.config.nifi_config.host = api_base
    nipyapi.security.set_service_auth_token(service="nifi", token=pat)

    print("Stopping process group %s ..." % pg_id, file=sys.stderr)
    nipyapi.canvas.schedule_process_group(pg_id, False)

    print("Disabling controller services ...", file=sys.stderr)
    nipyapi.canvas.schedule_all_controllers(pg_id, False)

    print("Purging queues ...", file=sys.stderr)
    nipyapi.canvas.purge_process_group(pg_id)

    print("Deleting process group ...", file=sys.stderr)
    nipyapi.canvas.delete_process_group(pg_id, force=True)

    print("Cleanup complete for %s" % pg_id, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Clean up a deployed NiFi process group from a Snowflake runtime"
    )
    parser.add_argument(
        "--pg-id", required=True, help="Process group UUID to remove"
    )
    parser.add_argument(
        "--runtime-url", required=True, help="Base URL of the Snowflake runtime"
    )
    parser.add_argument(
        "--pat", required=True, help="Personal Access Token for authentication"
    )
    args = parser.parse_args()

    try:
        cleanup(args.pg_id, args.runtime_url, args.pat)
    except Exception as exc:
        print("Cleanup failed for %s: %s" % (args.pg_id, exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
