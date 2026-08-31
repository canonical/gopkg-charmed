#!/usr/bin/env python3
"""Extract project-specific values from a downstream docs/conf.py.

Maps each value to the corresponding Copier question variable from
platform-engineering-documentation-files/copier.yml, and also extracts
non-Copier config values (extensions, intersphinx_mapping, etc.) that
need to be re-applied during onboarding.

Usage:
    python3 extract_conf_values.py docs/conf.py
    python3 extract_conf_values.py /path/to/downstream/docs/conf.py

Output: JSON object with two keys:
    "copier_values"       — Copier variable → extracted value
    "template_uncovered"  — config not covered by the template
"""

import ast
import json
import sys
from pathlib import Path


def extract_conf_values(conf_path: str) -> dict:
    """Parse a Sphinx conf.py and extract values mapped to Copier variables."""
    with open(conf_path, "r") as f:
        source = f.read()

    tree = ast.parse(source)

    result: dict = {}

    # ── Top-level assignments ──────────────────────────────────
    top_level_targets = {
        "project": "project",
        "author": "author",
        "ogp_image": "ogp_image",
        "html_favicon": "html_favicon",
        "html_title": "html_title",
    }

    # ── html_context dictionary entries ────────────────────────
    html_context_targets = {
        "product_page": "product_page",
        "product_tag": "product_tag",
        "discourse": "discourse",
        "mattermost": "mattermost",
        "matrix": "matrix",
        "github_url": "github_url",
        "repo_default_branch": "repo_default_branch",
        "repo_folder": "repo_folder",
        "display_contributors": "display_contributors",
    }

    # ── Non-Copier config (re-applied in Phase 6) ──────────────
    # These are configuration values NOT covered by the template
    # but that the downstream project may have customized.
    uncovered_targets = {
        "extensions",
        "intersphinx_mapping",
        "rst_prolog",
        "exclude_patterns",
        "html_css_files",
        "html_js_files",
        "html_static_path",
        "templates_path",
        "linkcheck_retries",
        "linkcheck_timeout",
        "sitemap_filename",
        "html_extra_path",
        "numfig",
        "nitpick_ignore",
        "nitpick_ignore_regex",
        "suppress_warnings",
    }

    uncovered: dict = {}  # Non-Copier config values

    # ── Walk the AST ───────────────────────────────────────────
    for node in ast.walk(tree):
        # Top-level assignments: project = "...", author = "...", etc.
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in top_level_targets:
                    value = _literal_value(node.value)
                    if value is not None:
                        result[top_level_targets[target.id]] = value

                # Non-Copier top-level assignments
                if isinstance(target, ast.Name) and target.id in uncovered_targets:
                    value = _extract_any_value(node.value)
                    if value is not None:
                        uncovered[target.id] = value

        # html_context = {...} dictionary
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "html_context":
                    if isinstance(node.value, ast.Dict):
                        for key, val in zip(node.value.keys, node.value.values):
                            key_str = _literal_value(key)
                            if key_str in html_context_targets:
                                value = _literal_value(val)
                                if value is not None:
                                    result[html_context_targets[key_str]] = value

    return {"copier_values": result, "template_uncovered": uncovered}


def _literal_value(node: ast.expr):
    """Safely extract a literal value from an AST node."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in ("True", "False"):
        return node.id == "True"
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        if isinstance(node.operand, ast.Constant):
            return -node.operand.value
    # Joined strings (f-strings) — return as string representation
    if isinstance(node, ast.JoinedStr):
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant):
                parts.append(str(val.value))
            elif isinstance(val, ast.FormattedValue):
                parts.append("{...}")
        return "".join(parts)
    return None


def _extract_any_value(node: ast.expr):
    """Extract a value from an AST node, handling lists, dicts, and literals.

    Returns a JSON-serializable Python value, or a string placeholder
    for values that cannot be statically resolved.
    """
    # Literals: strings, numbers, booleans, None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in ("True", "False"):
        return node.id == "True"
    if isinstance(node, ast.Name) and node.id == "None":
        return None

    # Lists: [item, item, ...]
    if isinstance(node, ast.List):
        return [_extract_any_value(elt) for elt in node.elts]

    # Tuples: (item, item, ...)
    if isinstance(node, ast.Tuple):
        return [_extract_any_value(elt) for elt in node.elts]

    # Dicts: {key: value, ...}
    if isinstance(node, ast.Dict):
        result = {}
        for k, v in zip(node.keys, node.values):
            key = _extract_any_value(k)
            val = _extract_any_value(v)
            if key is not None:
                result[str(key)] = val
        return result

    # Joined strings (f-strings)
    if isinstance(node, ast.JoinedStr):
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant):
                parts.append(str(val.value))
            elif isinstance(val, ast.FormattedValue):
                parts.append("{...}")
        return "".join(parts)

    # Function calls, attribute lookups, etc. — return a placeholder
    if isinstance(node, ast.Call):
        func_name = _get_name(node.func)
        return f"<call: {func_name}(...)>"

    if isinstance(node, ast.Attribute):
        return f"<attr: {_get_name(node)}>"

    # Unary minus
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        if isinstance(node.operand, ast.Constant):
            return -node.operand.value

    return None


def _get_name(node: ast.expr) -> str:
    """Get a dotted name string from an AST node (e.g., 'sphinx.util.inspect')."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _get_name(node.func)
    return "?"


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path/to/conf.py>", file=sys.stderr)
        sys.exit(1)

    conf_path = Path(sys.argv[1])
    if not conf_path.exists():
        print(f"Error: {conf_path} not found", file=sys.stderr)
        sys.exit(1)

    values = extract_conf_values(str(conf_path))
    print(json.dumps(values, indent=2))


if __name__ == "__main__":
    main()