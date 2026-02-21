import asyncio
from sqlalchemy import select
from app.database import async_session
from app.modules.users.models import Role, Permission, User
from app.core.security import hash_password

ROLES = [
    {"name": "super_admin", "description": "Full system access"},
    {"name": "admin", "description": "Administrative access"},
    {"name": "manager", "description": "Department manager"},
    {"name": "counselor", "description": "Student counselor"},
    {"name": "processor", "description": "Application processor"},
    {"name": "visa_officer", "description": "Visa processing officer"},
    {"name": "travel_ops", "description": "Travel operations"},
    {"name": "marketing_exec", "description": "Marketing executive"},
    {"name": "finance", "description": "Finance team"},
]

RESOURCES = ["leads", "students", "cases", "applications", "documents",
             "conversations", "tasks", "events", "approvals", "users", "courses", "reports"]
ACTIONS = ["read", "create", "update", "delete", "approve", "assign", "export"]


async def seed():
    async with async_session() as db:
        perm_map = {}
        for resource in RESOURCES:
            for action in ACTIONS:
                key = f"{resource}:{action}"
                existing = (await db.execute(
                    select(Permission).where(Permission.resource == resource, Permission.action == action)
                )).scalar_one_or_none()
                if existing:
                    perm_map[key] = existing
                else:
                    p = Permission(resource=resource, action=action)
                    db.add(p)
                    await db.flush()
                    perm_map[key] = p
        print(f"Permissions: {len(perm_map)}")

        for role_def in ROLES:
            existing = (await db.execute(select(Role).where(Role.name == role_def["name"]))).scalar_one_or_none()
            if not existing:
                role = Role(**role_def)
                if role.name in ("super_admin", "admin"):
                    role.permissions = list(perm_map.values())
                db.add(role)
                await db.flush()
                print(f"  Role: {role.name}")

        admin_email = "admin@empireo.in"
        if not (await db.execute(select(User).where(User.email == admin_email))).scalar_one_or_none():
            admin_role = (await db.execute(select(Role).where(Role.name == "super_admin"))).scalar_one()
            admin = User(email=admin_email, full_name="System Admin",
                         hashed_password=hash_password("EmpireAdmin@2024"), department="management")
            admin.roles.append(admin_role)
            db.add(admin)
            print(f"  Admin: {admin_email}")

        await db.commit()
        print("Done!")


if __name__ == "__main__":
    asyncio.run(seed())
