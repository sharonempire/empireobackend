from fastapi import Depends

from app.dependencies import require_perm


def include_router_with_default(app, router, prefix: str, resource: str):
    """Include a router into the FastAPI app and attach a default 'read' permission

    This applies a router-level dependency that requires `<resource>:read` for all
    endpoints, unless an endpoint overrides with a more specific dependency.
    """
    app.include_router(router, prefix=prefix, dependencies=[Depends(require_perm(resource, "read"))])
