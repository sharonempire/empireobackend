#!/usr/bin/env python3
"""Route permission linter — scans all FastAPI routes and flags any missing RBAC protection.

Usage:
    python scripts/lint_permissions.py

Checks every registered route and reports:
  - Routes with NO authentication dependency at all
  - Routes using only get_current_user (auth-only, no permission check)
  - Routes properly using require_perm() (shown as OK)

Exit codes:
  0  All routes are protected
  1  Unprotected routes found
"""
import ast
import sys
from pathlib import Path

# Paths
BASE = Path(__file__).resolve().parent.parent
MODULES = BASE / "app" / "modules"

SKIP_PREFIXES = ("/health", "/ready", "/docs", "/openapi.json", "/redoc")
AUTH_ROUTES = ("login", "refresh", "logout")  # these are intentionally public or self-auth


def scan_router_file(filepath: Path) -> list[dict]:
    """Parse a router.py and extract endpoint info."""
    with open(filepath) as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [{"file": str(filepath), "func": "PARSE_ERROR", "protection": "error"}]

    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef) and not isinstance(node, ast.FunctionDef):
            continue

        # Check if it's decorated with @router.get/post/patch/delete/put
        is_endpoint = False
        http_method = None
        path = None
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                attr_name = dec.func.attr
                if attr_name in ("get", "post", "patch", "put", "delete"):
                    is_endpoint = True
                    http_method = attr_name.upper()
                    if dec.args:
                        if isinstance(dec.args[0], ast.Constant):
                            path = dec.args[0].value

        if not is_endpoint:
            continue

        # Check function arguments for Depends(require_perm(...)) or Depends(get_current_user)
        protection = "NONE"
        for arg in node.args.args + node.args.kwonlyargs:
            # We need to check the defaults and kw_defaults
            pass

        # Check all Depends() calls in function defaults
        all_defaults = list(node.args.defaults) + list(node.args.kw_defaults)
        for default in all_defaults:
            if default is None:
                continue
            source_snippet = ast.dump(default)
            if "require_perm" in source_snippet:
                protection = "require_perm"
                break
            elif "get_current_user" in source_snippet:
                protection = "get_current_user"

        func_name = node.name
        results.append({
            "file": str(filepath.relative_to(BASE)),
            "func": func_name,
            "method": http_method or "?",
            "path": path or "?",
            "protection": protection,
        })

    return results


def main():
    all_results = []

    for router_file in sorted(MODULES.rglob("router.py")):
        results = scan_router_file(router_file)
        all_results.extend(results)

    # Categorize
    unprotected = []
    auth_only = []
    protected = []

    for r in all_results:
        # Skip auth endpoints (login/refresh are intentionally open)
        if any(name in r["func"] for name in AUTH_ROUTES):
            continue

        if r["protection"] == "require_perm":
            protected.append(r)
        elif r["protection"] == "get_current_user":
            auth_only.append(r)
        else:
            unprotected.append(r)

    # Report
    print("=" * 70)
    print("EMPIREO ROUTE PERMISSION LINT REPORT")
    print("=" * 70)

    print(f"\n{'Total endpoints scanned:':<35} {len(all_results)}")
    print(f"{'Protected (require_perm):':<35} {len(protected)}")
    print(f"{'Auth-only (get_current_user):':<35} {len(auth_only)}")
    print(f"{'UNPROTECTED (no auth):':<35} {len(unprotected)}")

    if unprotected:
        print("\n" + "!" * 70)
        print("CRITICAL — UNPROTECTED ROUTES (no authentication at all):")
        print("!" * 70)
        for r in unprotected:
            print(f"  {r['method']:>6} {r['path']:<40} {r['file']}::{r['func']}")

    if auth_only:
        print("\n" + "-" * 70)
        print("WARNING — Auth-only routes (no permission check):")
        print("-" * 70)
        for r in auth_only:
            print(f"  {r['method']:>6} {r['path']:<40} {r['file']}::{r['func']}")

    if protected:
        print("\n" + "-" * 70)
        print("OK — Properly protected routes:")
        print("-" * 70)
        for r in protected:
            print(f"  {r['method']:>6} {r['path']:<40} {r['file']}::{r['func']}")

    print()

    if unprotected or auth_only:
        print("RESULT: FAIL — some routes need permission enforcement")
        return 1
    else:
        print("RESULT: PASS — all routes properly protected")
        return 0


if __name__ == "__main__":
    sys.exit(main())
