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
import argparse
import json
import sys
import time

import nipyapi


def configure_nifi(runtime_url, pat):
    api_url = runtime_url.rstrip("/")
    if api_url.endswith("/nifi"):
        api_url = api_url[:-5]
    if not api_url.endswith("/nifi-api"):
        api_url += "/nifi-api"
    nipyapi.config.nifi_config.host = api_url
    nipyapi.config.nifi_config.api_key["bearerAuth"] = f"Bearer {pat}"
    nipyapi.config.nifi_config.api_client = None


def find_registry_client(name):
    api = nipyapi.nifi.ControllerApi()
    result = api.get_flow_registry_clients()
    for rc in (result.registries or []):
        if rc.component.name == name:
            return rc
    return None


def get_root_pg_id():
    return nipyapi.canvas.get_root_pg_id()


def resolve_version(registry_client_id, bucket_id, flow_id, version_spec):
    """Resolve a version spec to the actual version string.

    If version_spec is 'latest', fetches all versions from the registry and
    returns the version string of the most recent snapshot (by timestamp).
    Otherwise returns version_spec unchanged.
    """
    if version_spec != "latest":
        return version_spec

    api = nipyapi.nifi.FlowApi()
    result = api.get_versions(
        registry_id=registry_client_id,
        bucket_id=bucket_id,
        flow_id=flow_id,
    )
    snapshots = result.versioned_flow_snapshot_metadata_set or []
    if not snapshots:
        raise RuntimeError(
            f"No versions found for flow '{flow_id}' in bucket '{bucket_id}'"
        )
    latest = max(
        snapshots,
        key=lambda s: s.versioned_flow_snapshot_metadata.timestamp,
    )
    version = latest.versioned_flow_snapshot_metadata.version
    print(f"[flow] Resolved 'latest' -> '{version}' for {bucket_id}/{flow_id}")
    return version


def list_process_groups(parent_id=None):
    if parent_id is None:
        parent_id = get_root_pg_id()
    api = nipyapi.nifi.ProcessGroupsApi()
    result = api.get_process_groups(parent_id)
    return result.process_groups or []


def find_flow_pg_by_name(pg_name, parent_id=None):
    for pg in list_process_groups(parent_id):
        if pg.component.name == pg_name:
            return pg
    return None


def import_flow(registry_client_id, bucket, flow_name, version, pg_name, parent_id=None, dedicated_parameter_context=False):
    if parent_id is None:
        parent_id = get_root_pg_id()

    position = nipyapi.layout.suggest_pg_position(parent_id)

    api = nipyapi.nifi.ProcessGroupsApi()

    body = nipyapi.nifi.ProcessGroupEntity(
        revision=nipyapi.nifi.RevisionDTO(version=0),
        component=nipyapi.nifi.ProcessGroupDTO(
            name=pg_name,
            position=nipyapi.nifi.PositionDTO(x=position[0], y=position[1]),
            version_control_information=nipyapi.nifi.VersionControlInformationDTO(
                registry_id=registry_client_id,
                bucket_id=bucket,
                bucket_name=bucket,
                flow_id=flow_name,
                flow_name=flow_name,
                version=version,
            ),
        ),
    )

    strategy = "REPLACE" if dedicated_parameter_context else "KEEP_EXISTING"
    print(f"[flow] Importing {bucket}/{flow_name} '{version}' as '{pg_name}' (param context: {strategy})...")
    result = api.create_process_group(id=parent_id, body=body, parameter_context_handling_strategy=strategy)

    if result.component.name != pg_name:
        rename_body = nipyapi.nifi.ProcessGroupEntity(
            id=result.id,
            revision=result.revision,
            component=nipyapi.nifi.ProcessGroupDTO(
                id=result.id,
                name=pg_name,
            ),
        )
        result = api.update_process_group(id=result.id, body=rename_body)
        print(f"[flow] Renamed PG to '{pg_name}'")

    print(f"[flow] Imported '{pg_name}' (pg_id={result.id})")
    return result


def update_flow_version(pg_entity, new_version):
    vci = pg_entity.component.version_control_information
    print(f"[flow] Updating {vci.bucket_name}/{vci.flow_name} to '{new_version}'...")
    print(f"[flow] Current VCI state: '{vci.state}' — reverting local changes first...")

    try:
        nipyapi.versioning.revert_flow_ver(pg_entity, wait=True)
        print(f"[flow] Reverted local modifications")
    except Exception as e:
        print(f"[flow] Revert skipped or failed: {e}")

    import time
    time.sleep(2)
    api = nipyapi.nifi.ProcessGroupsApi()
    pg_entity = api.get_process_group(id=pg_entity.id)
    result = nipyapi.versioning.update_git_flow_ver(pg_entity, target_version=str(new_version))
    print(f"[flow] Updated to '{new_version}'")
    return result


def delete_flow(pg_entity):
    pg_id = pg_entity.id
    name = pg_entity.component.name
    print(f"[flow] Deleting process group '{name}' ({pg_id})...")

    nipyapi.canvas.schedule_process_group(pg_id, False)
    time.sleep(2)

    try:
        cs_api = nipyapi.nifi.FlowApi()
        cs_result = cs_api.get_controller_services_from_group(pg_id)
        for cs in (cs_result.controller_services or []):
            if cs.component.state == "ENABLED":
                nipyapi.canvas.schedule_controller(cs, False)
    except Exception:
        pass

    try:
        connections = nipyapi.nifi.ProcessGroupsApi().get_connections(pg_id)
        for conn in (connections.connections or []):
            drop_body = nipyapi.nifi.DropRequestEntity()
            nipyapi.nifi.FlowfileQueuesApi().create_drop_request(conn.id, body=drop_body)
    except Exception:
        pass

    time.sleep(2)
    api = nipyapi.nifi.ProcessGroupsApi()
    api.remove_process_group(pg_id, version=str(pg_entity.revision.version))
    print(f"[flow] Deleted process group '{name}'")


def reconcile_flows(flows, registry_client_name, runtime_url, nifi_pat):
    """Idempotent reconcile: create missing PGs, update version-mismatched PGs, skip up-to-date ones."""
    configure_nifi(runtime_url, nifi_pat)

    rc = find_registry_client(registry_client_name)
    if not rc:
        raise RuntimeError(f"Flow Registry Client '{registry_client_name}' not found")

    for flow_spec in flows:
        pg_name = flow_spec["name"]
        bucket = flow_spec["bucket"]
        flow_name = flow_spec["flow"]
        version_spec = flow_spec["version"]

        desired_version = resolve_version(rc.id, bucket, flow_name, version_spec)

        pg = find_flow_pg_by_name(pg_name)
        if not pg:
            import_flow(rc.id, bucket, flow_name, desired_version, pg_name,
                        dedicated_parameter_context=flow_spec.get("dedicated_parameter_context", False))
        else:
            vci = pg.component.version_control_information
            current_version = vci.version if vci else None
            if current_version != desired_version:
                print(f"[flow] '{pg_name}' is at '{current_version}', updating to '{desired_version}'...")
                update_flow_version(pg, desired_version)
            else:
                print(f"[flow] '{pg_name}' already at '{desired_version}' -- no change")


def start_flow(pg_id, pg_name=""):
    """Enable controller services in a PG then start all processors."""
    label = pg_name or pg_id
    print(f"[flow] Enabling controller services in '{label}'...")
    body = nipyapi.nifi.ActivateControllerServicesEntity(
        id=pg_id,
        state="ENABLED",
    )
    nipyapi.nifi.FlowApi().activate_controller_services(id=pg_id, body=body)
    time.sleep(3)
    print(f"[flow] Starting processors in '{label}'...")
    nipyapi.canvas.schedule_process_group(pg_id, True)
    print(f"[flow] '{label}' started")


def stop_flow(pg_id, pg_name=""):
    label = pg_name or pg_id
    print(f"[flow] Stopping processors in '{label}'...")
    nipyapi.canvas.schedule_process_group(pg_id, False)
    time.sleep(5)
    print(f"[flow] Disabling controller services in '{label}'...")
    body = nipyapi.nifi.ActivateControllerServicesEntity(
        id=pg_id,
        state="DISABLED",
    )
    nipyapi.nifi.FlowApi().activate_controller_services(id=pg_id, body=body)
    time.sleep(3)
    print(f"[flow] '{label}' stopped")


def delete_flows(flows, registry_client_name, runtime_url, nifi_pat):
    """Delete process groups for flows that were removed from config."""
    configure_nifi(runtime_url, nifi_pat)

    for flow_spec in flows:
        pg_name = flow_spec["name"]
        pg = find_flow_pg_by_name(pg_name)
        if pg:
            delete_flow(pg)
        else:
            print(f"[flow] '{pg_name}' not found, skipping delete")


def main():
    parser = argparse.ArgumentParser(description="Manage flows on NiFi runtime")
    parser.add_argument("action", choices=["reconcile", "delete"])
    parser.add_argument("--flows", required=True, help="JSON array of flow specs")
    parser.add_argument("--registry-client-name", default="nifihub")
    parser.add_argument("--runtime-url", required=True)
    parser.add_argument("--nifi-pat", required=True)
    args = parser.parse_args()

    flows = json.loads(args.flows)
    if args.action == "reconcile":
        reconcile_flows(flows, args.registry_client_name, args.runtime_url, args.nifi_pat)
    elif args.action == "delete":
        delete_flows(flows, args.registry_client_name, args.runtime_url, args.nifi_pat)


if __name__ == "__main__":
    main()