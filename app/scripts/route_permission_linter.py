"""Static route permission linter.

This linter does not import the FastAPI app. Instead it scans `app/modules/*/router.py`
files with AST to heuristically detect HTTP route handlers and whether they include
an auth/permission dependency such as `require_perm(` or `get_current_user` in the
function parameters or decorator arguments.

It is intentionally conservative and reports possible missing protections for
manual review. This avoids importing application code (useful when dependencies
aren't installed or DB/Redis are not running).

Usage:
    python3 -m app.scripts.route_permission_linter
"""
import ast
import glob
from pathlib import Path


def inspect_router_file(path: Path) -> list[str]:
    """Return list of route descriptions that look unprotected in the file."""
    text = path.read_text()
    tree = ast.parse(text, filename=str(path))

    unprotected = []

    # Find all function defs with decorators (likely route handlers)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check decorators for @router.get/post/put/delete/... presence
            has_route_decorator = False
            for deco in node.decorator_list:
                # decorator like router.get(...)
                if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute):
                    if getattr(deco.func.value, 'id', '') == 'router' or getattr(deco.func.value, 'attr', '') == 'router':
                        has_route_decorator = True
                elif isinstance(deco, ast.Attribute):
                    if getattr(deco.value, 'id', '') == 'router' or getattr(deco.value, 'attr', '') == 'router':
                        has_route_decorator = True

            if not has_route_decorator:
                continue

            # Heuristic: check function arguments for Depends(require_perm or get_current_user)
            protected = False
            for arg in node.args.defaults + node.args.kw_defaults:
                if arg is None:
                    continue
                src = ast.unparse(arg) if hasattr(ast, 'unparse') else ''
                if 'require_perm' in src or 'get_current_user' in src or 'Depends(require_perm' in src:
                    protected = True
                    break

            # Also check decorator keywords for dependencies
            if not protected:
                for deco in node.decorator_list:
                    if isinstance(deco, ast.Call):
                        for kw in deco.keywords:
                            try:
                                src = ast.unparse(kw.value) if hasattr(ast, 'unparse') else ''
                            except Exception:
                                src = ''
                            if 'require_perm' in src or 'get_current_user' in src:
                                protected = True
                                break
                        if protected:
                            break

            # Also check function body text for require_perm usage (loose heuristic)
            if not protected:
                body_src = ''.join(text.splitlines()[node.lineno - 1: node.end_lineno]) if hasattr(node, 'end_lineno') else ''
                if 'require_perm(' in body_src or 'get_current_user' in body_src:
                    protected = True

            if not protected:
                # Build a small signature for reporting
                name = node.name
                lineno = node.lineno
                unprotected.append(f"{path.relative_to(Path.cwd())}:{lineno} {name}()")

    return unprotected


def main():
    base = Path('app') / 'modules'
    pattern = str(base / '*' / 'router.py')
    files = glob.glob(pattern)
    all_unprotected = []

    for f in files:
        p = Path(f)
        try:
            unprot = inspect_router_file(p)
            all_unprotected.extend(unprot)
        except SyntaxError as e:
            print(f"Failed to parse {p}: {e}")

    if not all_unprotected:
        print('No obvious unprotected routes found (heuristic).')
    else:
        print('Possible unprotected routes (manual review required):')
        for u in all_unprotected:
            print('  ', u)


if __name__ == '__main__':
    main()
