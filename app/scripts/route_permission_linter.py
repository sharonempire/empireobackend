"""Simple route permission linter.

This script imports the FastAPI app and inspects registered routes. It reports
any route that does not include a permission check (heuristic) in its
dependencies. It's a developer tool — run in your dev environment after
including router defaults.

Usage:
    python -m app.scripts.route_permission_linter
"""
from typing import List
import inspect


def _dep_qualname(dep) -> str:
    try:
        fn = getattr(dep, "call", None) or dep.dependency
        if fn is None:
            return ""
        return getattr(fn, "__qualname__", getattr(fn, "__name__", ""))
    except Exception:
        return ""


def main():
    print("Loading app and inspecting routes...")
    from app.main import app  # import the FastAPI app

    missing: List[str] = []

    for route in app.routes:
        # Only HTTP routes
        if not hasattr(route, "methods"):
            continue
        # Gather dependency qualnames
        deps = []
        try:
            dependant = getattr(route, "dependant", None)
            if dependant and hasattr(dependant, "dependencies"):
                deps = [_dep_qualname(d) for d in dependant.dependencies]
        except Exception:
            deps = []

        # Heuristic: look for require_perm or get_current_user in dependency qualnames
        joined = " ".join(deps)
        has_perm = "require_perm" in joined or "get_current_user" in joined or "checker" in joined

        if not has_perm:
            missing.append(f"{','.join(sorted(route.methods))} {route.path}")

    if not missing:
        print("All inspected routes have a permission or auth dependency (heuristic).")
    else:
        print("Routes missing explicit permission/auth check (heuristic):")
        for r in missing:
            print("  ", r)


if __name__ == "__main__":
    main()
