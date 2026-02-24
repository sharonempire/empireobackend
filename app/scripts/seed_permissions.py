"""Seed roles and permissions from permissions.yaml.

Usage:
    python -m app.scripts.seed_permissions

Idempotent — safe to run repeatedly. Uses upsert logic.
"""
import uuid
import yaml
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.config import settings


def load_yaml() -> dict:
    path = Path(__file__).resolve().parent.parent.parent / "permissions.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def seed(session: Session, data: dict) -> None:
    roles_def = data["roles"]
    perms_def = data["permissions"]
    role_perms_def = data["role_permissions"]

    # 1. Upsert roles
    role_ids = {}
    for role_name, role_meta in roles_def.items():
        row = session.execute(
            text("SELECT id FROM eb_roles WHERE name = :name"),
            {"name": role_name},
        ).fetchone()
        if row:
            role_ids[role_name] = row[0]
            print(f"  Role '{role_name}' exists: {row[0]}")
        else:
            rid = uuid.uuid4()
            session.execute(
                text("INSERT INTO eb_roles (id, name, description) VALUES (:id, :name, :desc)"),
                {"id": rid, "name": role_name, "desc": role_meta.get("description", "")},
            )
            role_ids[role_name] = rid
            print(f"  Role '{role_name}' created: {rid}")

    # 2. Upsert permissions
    perm_ids = {}  # (resource, action) -> uuid
    for resource, meta in perms_def.items():
        for action in meta["actions"]:
            row = session.execute(
                text("SELECT id FROM eb_permissions WHERE resource = :r AND action = :a"),
                {"r": resource, "a": action},
            ).fetchone()
            if row:
                perm_ids[(resource, action)] = row[0]
            else:
                pid = uuid.uuid4()
                session.execute(
                    text(
                        "INSERT INTO eb_permissions (id, resource, action, description) "
                        "VALUES (:id, :r, :a, :desc)"
                    ),
                    {"id": pid, "r": resource, "a": action, "desc": f"{resource}:{action}"},
                )
                perm_ids[(resource, action)] = pid
                print(f"  Permission '{resource}:{action}' created")

    # 3. Assign permissions to roles
    all_perm_keys = list(perm_ids.keys())
    for role_name, mapping in role_perms_def.items():
        rid = role_ids[role_name]
        if mapping == "*":
            target_perms = all_perm_keys
        else:
            target_perms = []
            for resource, actions in mapping.items():
                for action in actions:
                    if (resource, action) in perm_ids:
                        target_perms.append((resource, action))

        # Clear existing role_permissions for this role, then re-insert
        session.execute(
            text("DELETE FROM eb_role_permissions WHERE role_id = :rid"),
            {"rid": rid},
        )
        for resource, action in target_perms:
            pid = perm_ids[(resource, action)]
            session.execute(
                text(
                    "INSERT INTO eb_role_permissions (role_id, permission_id) "
                    "VALUES (:rid, :pid) ON CONFLICT DO NOTHING"
                ),
                {"rid": rid, "pid": pid},
            )
        print(f"  Role '{role_name}' assigned {len(target_perms)} permissions")

    session.commit()
    print("\nSeed completed successfully.")


def main():
    print("Loading permissions.yaml...")
    data = load_yaml()

    db_url = settings.DATABASE_URL_SYNC
    if not db_url:
        raise RuntimeError("DATABASE_URL_SYNC not set")

    print(f"Connecting to database...")
    engine = create_engine(db_url)

    with Session(engine) as session:
        print("Seeding roles and permissions...\n")
        seed(session, data)

    engine.dispose()


if __name__ == "__main__":
    main()
