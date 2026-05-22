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
Generate GitHub wiki markdown pages from NiFi extension-manifest.xml files.

The nifi-nar-maven-plugin generates an extension-manifest.xml inside each NAR
module's target directory during the 'nar' packaging phase. This script finds
all such manifests under the extensions/ tree and converts them into structured
markdown suitable for a GitHub wiki.

Usage:
    python scripts/generate-wiki-docs.py [--extensions-dir extensions] [--output-dir wiki]
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def text(element, tag, default=""):
    """Extract text content from a child element."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return default


def text_bool(element, tag):
    """Extract boolean text from a child element."""
    return text(element, tag, "false") == "true"


def find_all(element, wrapper_tag, item_tag):
    """Find all items inside an optional wrapper element."""
    wrapper = element.find(wrapper_tag)
    if wrapper is not None:
        return wrapper.findall(item_tag)
    return []


def escape_md(value):
    """Escape pipe characters for markdown table cells."""
    if not value:
        return ""
    return value.replace("|", "\\|").replace("\n", " ")


def format_simple_class_name(fqcn):
    """Extract simple class name from a fully qualified class name."""
    return fqcn.rsplit(".", 1)[-1] if fqcn else fqcn


def generate_extension_page(extension_elem, nar_group, nar_artifact, nar_version):
    """Generate markdown for a single extension (processor, controller service, etc)."""
    name = text(extension_elem, "name")
    ext_type = text(extension_elem, "type")
    description = text(extension_elem, "description")
    simple_name = format_simple_class_name(name)

    lines = []
    lines.append(f"# {simple_name}")
    lines.append("")
    lines.append(f"**Full Class Name:** `{name}`")
    lines.append(f"**Type:** {ext_type}")
    lines.append(f"**Bundle:** `{nar_group}:{nar_artifact}:{nar_version}`")
    lines.append("")

    deprecation = extension_elem.find("deprecationNotice")
    if deprecation is not None:
        reason = text(deprecation, "reason", "This component is deprecated.")
        lines.append(f"> **Deprecated:** {reason}")
        lines.append("")

    if description:
        lines.append("## Description")
        lines.append("")
        lines.append(description)
        lines.append("")

    tags = find_all(extension_elem, "tags", "tag")
    if tags:
        tag_list = ", ".join(f"`{t.text.strip()}`" for t in tags if t.text)
        lines.append(f"**Tags:** {tag_list}")
        lines.append("")

    input_req = text(extension_elem, "inputRequirement")
    if input_req:
        lines.append(f"**Input Requirement:** {input_req}")
        lines.append("")

    properties = find_all(extension_elem, "properties", "property")
    if properties:
        lines.append("## Properties")
        lines.append("")
        lines.append("| Name | Description | Default Value | Required | EL Scope |")
        lines.append("|------|-------------|---------------|----------|----------|")
        for prop in properties:
            prop_display = escape_md(text(prop, "displayName") or text(prop, "name"))
            prop_desc = escape_md(text(prop, "description"))
            prop_default = escape_md(text(prop, "defaultValue"))
            prop_required = "Yes" if text_bool(prop, "required") else "No"
            el_scope = text(prop, "expressionLanguageScope", "")
            if el_scope == "NONE" or not el_scope:
                el_scope = ""
            lines.append(f"| {prop_display} | {prop_desc} | {prop_default} | {prop_required} | {el_scope} |")

            allowable = find_all(prop, "allowableValues", "allowableValue")
            if allowable:
                values = []
                for av in allowable:
                    av_display = text(av, "displayName") or text(av, "value")
                    values.append(f"`{av_display}`")
                lines.append(f"| | Allowable values: {', '.join(values)} | | | |")
        lines.append("")

    dynamic_props = find_all(extension_elem, "dynamicProperties", "dynamicProperty")
    if dynamic_props:
        lines.append("## Dynamic Properties")
        lines.append("")
        lines.append("| Name Pattern | Value | Description | EL Scope |")
        lines.append("|-------------|-------|-------------|----------|")
        for dp in dynamic_props:
            dp_name = escape_md(text(dp, "name"))
            dp_value = escape_md(text(dp, "value"))
            dp_desc = escape_md(text(dp, "description"))
            dp_el = text(dp, "expressionLanguageScope", "")
            lines.append(f"| {dp_name} | {dp_value} | {dp_desc} | {dp_el} |")
        lines.append("")

    relationships = find_all(extension_elem, "relationships", "relationship")
    if relationships:
        lines.append("## Relationships")
        lines.append("")
        lines.append("| Name | Description | Auto-Terminated |")
        lines.append("|------|-------------|-----------------|")
        for rel in relationships:
            rel_name = escape_md(text(rel, "name"))
            rel_desc = escape_md(text(rel, "description"))
            rel_auto = "Yes" if text_bool(rel, "autoTerminated") else "No"
            lines.append(f"| {rel_name} | {rel_desc} | {rel_auto} |")
        lines.append("")

    reads_attrs = find_all(extension_elem, "readsAttributes", "readsAttribute")
    if reads_attrs:
        lines.append("## Reads Attributes")
        lines.append("")
        lines.append("| Name | Description |")
        lines.append("|------|-------------|")
        for attr in reads_attrs:
            lines.append(f"| {escape_md(text(attr, 'name'))} | {escape_md(text(attr, 'description'))} |")
        lines.append("")

    writes_attrs = find_all(extension_elem, "writesAttributes", "writesAttribute")
    if writes_attrs:
        lines.append("## Writes Attributes")
        lines.append("")
        lines.append("| Name | Description |")
        lines.append("|------|-------------|")
        for attr in writes_attrs:
            lines.append(f"| {escape_md(text(attr, 'name'))} | {escape_md(text(attr, 'description'))} |")
        lines.append("")

    stateful = extension_elem.find("stateful")
    if stateful is not None:
        state_desc = text(stateful, "description")
        scopes = find_all(stateful, "scopes", "scope")
        scope_text = ", ".join(s.text.strip() for s in scopes if s.text) if scopes else text(stateful, "scope")
        lines.append("## State Management")
        lines.append("")
        lines.append(f"**Scopes:** {scope_text}")
        lines.append("")
        if state_desc:
            lines.append(state_desc)
            lines.append("")

    restricted = extension_elem.find("restricted")
    if restricted is not None:
        lines.append("## Restricted")
        lines.append("")
        general_restriction = text(restricted, "generalRestrictionExplanation")
        if general_restriction:
            lines.append(general_restriction)
            lines.append("")
        restrictions = find_all(restricted, "restrictions", "restriction")
        for r in restrictions:
            req_perm = text(r, "requiredPermission")
            explanation = text(r, "explanation")
            lines.append(f"- **{req_perm}**: {explanation}")
        if restrictions:
            lines.append("")

    use_cases = find_all(extension_elem, "useCases", "useCase")
    if use_cases:
        lines.append("## Use Cases")
        lines.append("")
        for uc in use_cases:
            uc_desc = text(uc, "description")
            uc_notes = text(uc, "notes")
            uc_keywords = find_all(uc, "keywords", "keyword")
            lines.append(f"### {uc_desc}")
            lines.append("")
            if uc_keywords:
                kw_list = ", ".join(f"`{kw.text.strip()}`" for kw in uc_keywords if kw.text)
                lines.append(f"**Keywords:** {kw_list}")
                lines.append("")
            if uc_notes:
                lines.append(uc_notes)
                lines.append("")
            uc_config = text(uc, "configuration")
            if uc_config:
                lines.append("**Configuration:**")
                lines.append("")
                lines.append(uc_config)
                lines.append("")

    see_also = find_all(extension_elem, "seeAlso", "see")
    if see_also:
        see_names = [format_simple_class_name(s.text.strip()) for s in see_also if s.text]
        links = [f"[{n}]({n})" for n in see_names]
        lines.append(f"**See Also:** {', '.join(links)}")
        lines.append("")

    return simple_name, "\n".join(lines)


def process_manifest(manifest_path, extensions_dir):
    """Parse an extension-manifest.xml and return a list of (page_name, markdown) tuples."""
    tree = ET.parse(manifest_path)
    root = tree.getroot()

    nar_group = text(root, "groupId", "unknown")
    nar_artifact = text(root, "artifactId", "unknown")
    nar_version = text(root, "version", "unknown")

    bundle_rel_path = os.path.relpath(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(manifest_path)))),
        extensions_dir
    )

    pages = []
    extensions_elem = root.find("extensions")
    if extensions_elem is not None:
        for ext in extensions_elem.findall("extension"):
            page_name, markdown = generate_extension_page(ext, nar_group, nar_artifact, nar_version)
            pages.append((page_name, markdown, nar_group, nar_artifact, nar_version, bundle_rel_path))

    return pages


def generate_components_page(all_pages):
    """Generate the Components.md wiki index page."""
    lines = []
    lines.append("# Components")
    lines.append("")
    lines.append("> Auto-generated from extension manifests. Updated automatically when extensions are merged into `main`.")
    lines.append("")

    bundles = {}
    for page_name, _, nar_group, nar_artifact, nar_version, bundle_rel_path in all_pages:
        key = (nar_group, nar_artifact, nar_version, bundle_rel_path)
        if key not in bundles:
            bundles[key] = []
        bundles[key].append(page_name)

    for (group, artifact, version, rel_path), components in sorted(bundles.items()):
        lines.append(f"## {artifact} ({version})")
        lines.append("")
        lines.append(f"**Group:** `{group}` | **Path:** `extensions/{rel_path}`")
        lines.append("")
        for comp_name in sorted(components):
            lines.append(f"- [{comp_name}]({comp_name})")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate wiki docs from NiFi extension manifests")
    parser.add_argument("--extensions-dir", default="extensions", help="Path to the extensions directory")
    parser.add_argument("--output-dir", default="wiki", help="Output directory for wiki markdown files")
    args = parser.parse_args()

    extensions_dir = os.path.abspath(args.extensions_dir)
    output_dir = os.path.abspath(args.output_dir)

    if not os.path.isdir(extensions_dir):
        print(f"Extensions directory not found: {extensions_dir}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    manifest_files = []
    for root_dir, dirs, files in os.walk(extensions_dir):
        for f in files:
            if f == "extension-manifest.xml":
                full_path = os.path.join(root_dir, f)
                if "target" in full_path and "META-INF" in full_path:
                    manifest_files.append(full_path)

    if not manifest_files:
        print("No extension-manifest.xml files found. Ensure bundles have been built.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(manifest_files)} extension manifest(s)")

    all_pages = []
    for manifest in manifest_files:
        print(f"  Processing: {os.path.relpath(manifest)}")
        pages = process_manifest(manifest, extensions_dir)
        all_pages.extend(pages)

    for page_name, markdown, *_ in all_pages:
        safe_name = page_name.replace("/", "-")
        output_path = os.path.join(output_dir, f"{safe_name}.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"  Generated: {safe_name}.md")

    components_md = generate_components_page(all_pages)
    components_path = os.path.join(output_dir, "Components.md")
    with open(components_path, "w", encoding="utf-8") as f:
        f.write(components_md)
    print(f"  Generated: Components.md")

    print(f"\nGenerated {len(all_pages)} component page(s) + Components.md in {output_dir}")


if __name__ == "__main__":
    main()
