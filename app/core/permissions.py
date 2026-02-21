from fastapi import HTTPException, status
from app.modules.users.models import User


def require_permissions(*required: str):
    """Check if user has required permissions. Usage: Depends(require_permissions("leads:read"))"""
    def dependency(current_user: User):
        user_perms = set()
        for role in current_user.roles:
            for perm in role.permissions:
                user_perms.add(f"{perm.resource}:{perm.action}")
        role_names = {r.name for r in current_user.roles}
        if "super_admin" in role_names:
            return current_user
        for req in required:
            if req not in user_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission: {req}",
                )
        return current_user
    return dependency
