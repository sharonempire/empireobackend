from fastapi import Depends

from app.dependencies import get_current_user


def include_router_with_default(app, router, prefix: str, resource: str):
    """Include a router into the FastAPI app with authentication required.

    All endpoints require a valid JWT (authenticated user). Individual
    endpoints handle their own permission checks for write operations
    via require_perm() where needed.
    """
    app.include_router(router, prefix=prefix, dependencies=[Depends(get_current_user)])
