#!/usr/bin/env python3
"""
Seed script for local Postgres with Empireo reference data.

Runs standalone (not inside FastAPI). Uses the app's sync database
engine and security helpers.

Usage (inside Docker):
    python scripts/seed_local.py

Usage (outside Docker, with .env loaded):
    python scripts/seed_local.py
"""

import sys
import os

# Ensure the project root is on sys.path so `app.*` imports resolve.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

from app.database import sync_session_factory
from app.core.security import hash_password

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HASHED_PW = hash_password("Empire@2025")


def _run(session, label: str, sql: str, params=None):
    """Execute a SQL statement, print progress, and return the result."""
    print(f"  -> {label} ... ", end="", flush=True)
    result = session.execute(text(sql), params or {})
    session.commit()
    print("OK")
    return result


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

ROLES = [
    ("7c70815a-605e-4c5a-b54c-c1380175bae9", "admin", "Full system access. Can manage users, roles, and all entities."),
    ("28506fbd-4521-456c-9959-07e1c7a60247", "counselor", "Manages students, cases, and applications. Can create tasks."),
    ("544b1f0b-6228-40ad-b999-2d29065618c8", "processor", "Handles document processing, visa applications, and case stages."),
    ("ca1ea8e0-2408-4b97-8ce2-6633697e70fe", "viewer", "Read-only access to dashboards and reports."),
    ("50ea6d03-de51-45fd-81cb-0ea6a37d442f", "visa_officer", "Reviews visa cases, approves/rejects applications."),
]

PERMISSIONS = [
    ("03280f49-b883-4ed7-9a69-962f0dfdcfb3", "actions", "approve"),
    ("33cbe1ca-8760-4988-8ce0-d4635c30d480", "actions", "create"),
    ("94af6612-2d39-4fe3-bd4d-45894bbcd20a", "actions", "read"),
    ("6aa8c5df-f1dd-48f3-9b11-40dccc53bab8", "ai_artifacts", "create"),
    ("78091e5a-ba40-4983-a854-cb6a66fdfcaa", "ai_artifacts", "read"),
    ("8f63f6cc-40d7-4818-bc82-e19dd1d1cd7e", "applications", "create"),
    ("3f38aac7-c254-4fc6-87ef-cc021ff1bece", "applications", "delete"),
    ("8531567c-f5df-4ed3-8a91-4a67b2534e43", "applications", "read"),
    ("48008466-1906-4c65-8b7c-429660775724", "applications", "update"),
    ("88db68ba-6791-4098-9523-fe334f6fcf1a", "cases", "assign"),
    ("0cee66b1-4fdb-4d32-8f87-61b22d942b4d", "cases", "create"),
    ("a7afef7a-9ce1-4e7b-8e64-928a7de5184c", "cases", "delete"),
    ("efd0fc41-9c32-4819-a27a-4fc800ad0ea2", "cases", "read"),
    ("068913e3-c985-4712-9a63-73c1a1962497", "cases", "update"),
    ("c53a6573-1ff9-4350-89c6-3e0e69e00d22", "documents", "create"),
    ("fd0375ed-4a72-44a9-8553-f0c8ee52e59c", "documents", "delete"),
    ("b6305b05-c86e-42a6-8769-0af46fbcefad", "documents", "read"),
    ("7631b5ce-6758-4e64-9d8e-57ea87326327", "documents", "update"),
    ("3a978473-36f7-437e-8a2a-70e30943b786", "documents", "verify"),
    ("88194b39-60ae-4cf6-9daa-59efdc1928d3", "events", "read"),
    ("b69bd404-ffa6-45f7-8be4-aebf277fcb5d", "notifications", "create"),
    ("2ba466bb-ea9b-45b5-88f9-a2f1d68ad850", "notifications", "read"),
    ("0e96bf72-c068-4f5e-9a4a-89f5f0996729", "policies", "create"),
    ("1c93857a-2640-409e-bace-d539560cea5b", "policies", "read"),
    ("c5a2a0a0-a46c-4a49-a8f4-b79c59b8bda8", "policies", "update"),
    ("3578a4f7-2145-4989-b8b2-2122fab4ea7f", "reports", "read"),
    ("4ebe9927-a8d2-41b0-b96a-d2bda887bbd5", "roles", "manage"),
    ("2978b68b-4753-4883-805f-edd5ef7ab615", "students", "create"),
    ("c2270deb-37f8-42b5-8b20-0fd2c67d52ec", "students", "delete"),
    ("69a85121-4a9f-4aaf-aceb-cc34973c5eaf", "students", "read"),
    ("474fd6d8-fa72-4106-a845-e93c00d0d505", "students", "update"),
    ("36041686-5ffd-4304-bb10-1eb89e1c0da9", "tasks", "assign"),
    ("8e042951-0695-4021-95a5-9fd0f7e28ce6", "tasks", "create"),
    ("81836c3a-fd35-4355-a580-d87d4126909b", "tasks", "delete"),
    ("3fdb188c-d08a-40f4-b88c-8fc167f8075e", "tasks", "read"),
    ("7ecd0efb-a4d9-4b9e-8e6b-ea0bcd1708bc", "tasks", "update"),
    ("2fd1b217-8ca2-420a-8d3c-c362e6d57759", "users", "create"),
    ("9ac46132-dff4-4c3a-afff-a0925d98d73d", "users", "delete"),
    ("751498ea-0e93-4bb8-acbd-058928a5f641", "users", "read"),
    ("78af61aa-eaeb-403b-960e-4ccb94c1008d", "users", "update"),
    ("2c660045-56f1-431c-bb7e-e429b9992a01", "workflows", "create"),
    ("064f5be6-16c0-4347-8ff1-52859563a03f", "workflows", "manage"),
    ("97670edf-cdcd-47e1-ba2d-ecc7e4893aee", "workflows", "read"),
    ("4282537a-995d-49fd-a3ec-4fa17951a351", "workflows", "update"),
    # Module permissions (added for Flutter frontend)
    ("a0000001-0000-0000-0000-000000000001", "attendance", "read"),
    ("a0000001-0000-0000-0000-000000000002", "attendance", "create"),
    ("a0000001-0000-0000-0000-000000000003", "attendance", "update"),
    ("a0000001-0000-0000-0000-000000000004", "attendance", "delete"),
    ("a0000001-0000-0000-0000-000000000005", "call_events", "read"),
    ("a0000001-0000-0000-0000-000000000006", "call_events", "create"),
    ("a0000001-0000-0000-0000-000000000007", "leads", "read"),
    ("a0000001-0000-0000-0000-000000000008", "leads", "create"),
    ("a0000001-0000-0000-0000-000000000009", "leads", "update"),
    ("a0000001-0000-0000-0000-000000000010", "leads", "delete"),
    ("a0000001-0000-0000-0000-000000000011", "profiles", "read"),
    ("a0000001-0000-0000-0000-000000000012", "profiles", "update"),
    ("a0000001-0000-0000-0000-000000000013", "courses", "read"),
    ("a0000001-0000-0000-0000-000000000014", "courses", "update"),
    ("a0000001-0000-0000-0000-000000000015", "chat", "read"),
    ("a0000001-0000-0000-0000-000000000016", "chat", "create"),
    ("a0000001-0000-0000-0000-000000000017", "geography", "read"),
    ("a0000001-0000-0000-0000-000000000018", "intakes", "read"),
    ("a0000001-0000-0000-0000-000000000019", "jobs", "read"),
    ("a0000001-0000-0000-0000-000000000020", "ig_sessions", "read"),
    ("a0000001-0000-0000-0000-000000000021", "ig_sessions", "update"),
    ("a0000001-0000-0000-0000-000000000022", "analytics", "read"),
]

# (id, email, full_name, department, is_active, legacy_supabase_id, phone, caller_id, location, countries_json)
# countries_json should be a JSON string or None
USERS = [
    ("6d4c5c25-0dac-4a0f-b84e-ea0007cab2cc", "sharon@empireoe.com", "Sharon", "Administration", True, "f8ba170e-283c-45a1-8ebe-286abe23eb0b", "8129130745", "918129130745", "Kochi, kerala", None),
    ("38858f62-5e32-4ab4-8a03-4060ef341620", "web@empireoe.com", "Abel", "Administration", True, "c05d2b75-b75c-4116-bf1f-927b713bddd9", "917356533368", None, None, None),
    ("50279461-119f-4d17-9a13-b99806ec1cec", "aleena@empireoe.com", "Aleena", "Counseling", True, "9abe89b4-7f53-4462-bb21-644ee51745ef", "918891390647", "918031495052", None, None),
    ("a51364c3-a61c-4889-b80e-692c8958aa79", "anagha@empireoe.com", "Anagha", "Operations", True, "b28e04d5-0942-455a-b5b6-88773bb0b1c7", None, None, None, '["Poland","Georgia"]'),
    ("8877a9d3-5cbb-47a3-9d35-1c792e284b61", "aneetta@empireoe.com", "Aneetta", "Operations", True, "fd309106-a417-491b-b439-ce3ba1bb35db", None, None, None, '["Latvia"]'),
    ("763aa600-8f5c-4a97-bdb5-13dc1aefed29", "bhavyatha@empireoe.com", "Bhavyatha", "Counseling", True, "24bf40cc-5b6b-40c2-8793-6afa242b849f", "918075558495", "918031495051", None, None),
    ("a48ff5b4-537a-4b56-962a-613218d17f51", "dilna@empireoe.com", "dilna", "Operations", True, "5dcc0c30-2586-4b59-a3f3-80149913cf9b", None, None, None, '["Georgia"]'),
    ("179f0578-8a91-420c-be2c-7044eb222ec9", "gopika@empireoe.com", "Gopika", "Operations", True, "8751c745-d58b-4e90-bd23-318b57882de2", None, None, None, '["Lithuania","Malta","Latvia"]'),
    ("7b026f6c-5bd3-4505-b896-1eca2d76da40", "harish@empireoe.com", "Harish S", "Administration", True, "1db4ec15-4101-4e85-a63c-4da109c79197", None, None, None, None),
    ("513965b4-d61c-45f4-893a-c5cbf4c008a8", "jubin.joseph@empireoe.com", "Jubin", "Counseling", True, "63dea1ac-b43b-4514-b866-1e0c2f8ec63c", "8714980666", "918031495056", None, None),
    ("0238f2be-22b9-4851-8944-a0a489b4baf3", "karthika@empireoe.com", "Karthika", "Suspended", False, "8ecd5b6e-55ba-4017-8466-7925758894c9", None, None, None, None),
    ("e324740b-e7ef-4b06-81df-ef9a65fc6a2c", "krishna@empireoe.com", "Krishna", "Operations", True, "b71945eb-e9b7-4ea9-8c84-03cc47714232", None, None, None, '["Lithuania"]'),
    ("e17f9694-78a8-4ce1-a7ba-1c0056da2768", "mano@empireoe.com", "Mano", "Administration", True, "93b0c827-fc53-484d-8e76-6a100a6fe296", None, None, None, None),
    ("b59d84a0-c5b1-4551-84a8-254843bbea50", "mrfunnyshorts55@gmail.com", "pulling off", "Operations", True, "d3055591-a852-434b-89c9-d60b464b7f53", "917727243788", None, None, None),
    ("2ab67469-8143-41f2-8b60-c28e7b15c288", "renu@empireoe.com", "Renu V Menon", "Suspended", False, "0bad3787-e95f-49f9-b07f-634ec1e6e318", "919633004738", "918031495054", None, None),
    ("3c8d77b5-f3db-4fb9-9a23-45d721d4240f", "shybin@empireoe.com", "Shybin Biju", "Counseling", True, "4fb62a56-3955-48ae-9bf6-8dd0159a631c", "917012304094", "918069637150", None, None),
    ("4513a7e0-988d-4c9a-b684-60d2c0b046b8", "sreekuttan@empireoe.com", "Sreekuttan Empire", "Counseling", True, "cbcf5f6d-497c-4d4d-8bdd-7f9412896760", "919778520897", "918031495053", "Ernakulam", None),
    ("acb49ef6-e96f-4bd0-b53f-ada1ed616d0f", "timy@empireoe.com", "Timy", "Operations", True, "4e9afa2a-adf0-4cb7-9439-32f5c443db7e", None, None, None, '["Malta"]'),
    ("4b62d8a2-1724-41cd-9b79-df1cef987767", "tizna@empireoe.com", "Tisna Antony", "Suspended", False, "7453588a-f97c-4f8a-bc53-22804db99025", "916282584644", "918031495054", None, None),
]

# (user_id, role_id)
USER_ROLES = [
    ("6d4c5c25-0dac-4a0f-b84e-ea0007cab2cc", "7c70815a-605e-4c5a-b54c-c1380175bae9"),  # sharon -> admin
    ("38858f62-5e32-4ab4-8a03-4060ef341620", "7c70815a-605e-4c5a-b54c-c1380175bae9"),  # abel -> admin
    ("50279461-119f-4d17-9a13-b99806ec1cec", "28506fbd-4521-456c-9959-07e1c7a60247"),  # aleena -> counselor
    ("a51364c3-a61c-4889-b80e-692c8958aa79", "544b1f0b-6228-40ad-b999-2d29065618c8"),  # anagha -> processor
    ("8877a9d3-5cbb-47a3-9d35-1c792e284b61", "544b1f0b-6228-40ad-b999-2d29065618c8"),  # aneetta -> processor
    ("763aa600-8f5c-4a97-bdb5-13dc1aefed29", "28506fbd-4521-456c-9959-07e1c7a60247"),  # bhavyatha -> counselor
    ("a48ff5b4-537a-4b56-962a-613218d17f51", "544b1f0b-6228-40ad-b999-2d29065618c8"),  # dilna -> processor
    ("179f0578-8a91-420c-be2c-7044eb222ec9", "544b1f0b-6228-40ad-b999-2d29065618c8"),  # gopika -> processor
    ("7b026f6c-5bd3-4505-b896-1eca2d76da40", "7c70815a-605e-4c5a-b54c-c1380175bae9"),  # harish -> admin
    ("513965b4-d61c-45f4-893a-c5cbf4c008a8", "28506fbd-4521-456c-9959-07e1c7a60247"),  # jubin -> counselor
    ("0238f2be-22b9-4851-8944-a0a489b4baf3", "ca1ea8e0-2408-4b97-8ce2-6633697e70fe"),  # karthika -> viewer
    ("e324740b-e7ef-4b06-81df-ef9a65fc6a2c", "544b1f0b-6228-40ad-b999-2d29065618c8"),  # krishna -> processor
    ("e17f9694-78a8-4ce1-a7ba-1c0056da2768", "7c70815a-605e-4c5a-b54c-c1380175bae9"),  # mano -> admin
    ("b59d84a0-c5b1-4551-84a8-254843bbea50", "544b1f0b-6228-40ad-b999-2d29065618c8"),  # mrfunnyshorts55 -> processor
    ("2ab67469-8143-41f2-8b60-c28e7b15c288", "ca1ea8e0-2408-4b97-8ce2-6633697e70fe"),  # renu -> viewer
    ("3c8d77b5-f3db-4fb9-9a23-45d721d4240f", "28506fbd-4521-456c-9959-07e1c7a60247"),  # shybin -> counselor
    ("4513a7e0-988d-4c9a-b684-60d2c0b046b8", "28506fbd-4521-456c-9959-07e1c7a60247"),  # sreekuttan -> counselor
    ("acb49ef6-e96f-4bd0-b53f-ada1ed616d0f", "544b1f0b-6228-40ad-b999-2d29065618c8"),  # timy -> processor
    ("4b62d8a2-1724-41cd-9b79-df1cef987767", "ca1ea8e0-2408-4b97-8ce2-6633697e70fe"),  # tizna -> viewer
]

# All 44 permission IDs for reference
ALL_PERM_IDS = [p[0] for p in PERMISSIONS]

# Build permission lookup by (resource, action) -> id
PERM_LOOKUP = {(p[1], p[2]): p[0] for p in PERMISSIONS}

# Role permission assignments
# admin -> ALL 44 permissions
ADMIN_ROLE_ID = "7c70815a-605e-4c5a-b54c-c1380175bae9"
COUNSELOR_ROLE_ID = "28506fbd-4521-456c-9959-07e1c7a60247"
PROCESSOR_ROLE_ID = "544b1f0b-6228-40ad-b999-2d29065618c8"
VIEWER_ROLE_ID = "ca1ea8e0-2408-4b97-8ce2-6633697e70fe"
VISA_OFFICER_ROLE_ID = "50ea6d03-de51-45fd-81cb-0ea6a37d442f"

# Counselor gets everything EXCEPT users:create, users:delete, users:update, roles:manage
COUNSELOR_EXCLUDED = {
    PERM_LOOKUP[("users", "create")],
    PERM_LOOKUP[("users", "delete")],
    PERM_LOOKUP[("users", "update")],
    PERM_LOOKUP[("roles", "manage")],
}
COUNSELOR_PERM_IDS = [pid for pid in ALL_PERM_IDS if pid not in COUNSELOR_EXCLUDED]

# Processor: documents (all), cases (read, update, assign), applications (read, update, create),
# students (read, update), tasks (read, create, update, assign), events (read),
# notifications (read, create), reports (read), ai_artifacts (read),
# policies (read), workflows (read), actions (read, create)
PROCESSOR_PERMS = [
    ("documents", "create"), ("documents", "delete"), ("documents", "read"),
    ("documents", "update"), ("documents", "verify"),
    ("cases", "read"), ("cases", "update"), ("cases", "assign"),
    ("applications", "read"), ("applications", "update"), ("applications", "create"),
    ("students", "read"), ("students", "update"),
    ("tasks", "read"), ("tasks", "create"), ("tasks", "update"), ("tasks", "assign"),
    ("events", "read"),
    ("notifications", "read"), ("notifications", "create"),
    ("reports", "read"),
    ("ai_artifacts", "read"),
    ("policies", "read"),
    ("workflows", "read"),
    ("actions", "read"), ("actions", "create"),
    ("users", "read"),
    ("attendance", "read"), ("attendance", "create"), ("attendance", "update"),
    ("call_events", "read"), ("leads", "read"),
    ("profiles", "read"), ("courses", "read"), ("geography", "read"),
]
PROCESSOR_PERM_IDS = [PERM_LOOKUP[k] for k in PROCESSOR_PERMS]

# Visa officer: similar to processor + cases (create, delete), applications (delete)
VISA_OFFICER_PERMS = PROCESSOR_PERMS + [
    ("cases", "create"), ("cases", "delete"),
    ("applications", "delete"),
]
VISA_OFFICER_PERM_IDS = list(dict.fromkeys([PERM_LOOKUP[k] for k in VISA_OFFICER_PERMS]))

# Viewer: read-only permissions only
VIEWER_PERMS = [
    ("actions", "read"),
    ("ai_artifacts", "read"),
    ("applications", "read"),
    ("cases", "read"),
    ("documents", "read"),
    ("events", "read"),
    ("notifications", "read"),
    ("policies", "read"),
    ("reports", "read"),
    ("students", "read"),
    ("tasks", "read"),
    ("users", "read"),
    ("workflows", "read"),
    ("attendance", "read"), ("call_events", "read"), ("leads", "read"),
    ("profiles", "read"), ("courses", "read"), ("chat", "read"),
    ("geography", "read"), ("intakes", "read"), ("jobs", "read"),
]
VIEWER_PERM_IDS = [PERM_LOOKUP[k] for k in VIEWER_PERMS]

# Collect all role_permission rows: (role_id, permission_id)
ROLE_PERMISSIONS: list[tuple[str, str]] = []
# Admin -> all
for pid in ALL_PERM_IDS:
    ROLE_PERMISSIONS.append((ADMIN_ROLE_ID, pid))
# Counselor
for pid in COUNSELOR_PERM_IDS:
    ROLE_PERMISSIONS.append((COUNSELOR_ROLE_ID, pid))
# Processor
for pid in PROCESSOR_PERM_IDS:
    ROLE_PERMISSIONS.append((PROCESSOR_ROLE_ID, pid))
# Visa officer
for pid in VISA_OFFICER_PERM_IDS:
    ROLE_PERMISSIONS.append((VISA_OFFICER_ROLE_ID, pid))
# Viewer
for pid in VIEWER_PERM_IDS:
    ROLE_PERMISSIONS.append((VIEWER_ROLE_ID, pid))

# Profiles: (id, diplay_name, profilepicture, designation, phone, email, callerId, location, countries, user_type, freelancer_status, fcm_token, user_id)
STORAGE_BASE = "https://ebgzlzemrargfahwokti.supabase.co/storage/v1/object/public/user_images"
PROFILES = [
    (
        "9abe89b4-7f53-4462-bb21-644ee51745ef", "Aleena",
        f"{STORAGE_BASE}/profile_1764564552980.png",
        "Counsellor", 918891390647, "aleena@empireoe.com", "918031495052",
        None, None, None, None, None, None,
    ),
    (
        "b28e04d5-0942-455a-b5b6-88773bb0b1c7", "Anagha",
        None,
        "Country Head", None, "anagha@empireoe.com", None,
        None, ["Poland", "Georgia"], None, None, None, None,
    ),
    (
        "fd309106-a417-491b-b439-ce3ba1bb35db", "Aneetta",
        None,
        "Country Head", None, "aneetta@empireoe.com", None,
        None, ["Latvia"], None, None, None, None,
    ),
    (
        "24bf40cc-5b6b-40c2-8793-6afa242b849f", "Bhavyatha",
        f"{STORAGE_BASE}/profile_1763448854819.png",
        "Counsellor", 918075558495, "bhavyatha@empireoe.com", "918031495051",
        None, None, None, None, None, None,
    ),
    (
        "5dcc0c30-2586-4b59-a3f3-80149913cf9b", "dilna",
        None,
        "Country Head", None, "dilna@empireoe.com", None,
        None, ["Georgia"], None, None, None, None,
    ),
    (
        "8751c745-d58b-4e90-bd23-318b57882de2", "Gopika",
        None,
        "Country Head", None, "gopika@empireoe.com", None,
        None, ["Lithuania", "Malta", "Latvia"], None, None, None, None,
    ),
    (
        "1db4ec15-4101-4e85-a63c-4da109c79197", "Harish S",
        None,
        "Admin", None, "harish@empireoe.com", None,
        None, None, None, None, None, None,
    ),
    (
        "63dea1ac-b43b-4514-b866-1e0c2f8ec63c", "Jubin",
        f"{STORAGE_BASE}/profile_1772018438866.png",
        "Counsellor", 8714980666, "jubin.joseph@empireoe.com", "918031495056",
        None, None, None, None, None, None,
    ),
    (
        "8ecd5b6e-55ba-4017-8466-7925758894c9", "Karthika",
        f"{STORAGE_BASE}/profile_1762852292113.png",
        "Suspend", None, "karthika@empireoe.com", None,
        None, None, None, None, None, None,
    ),
    (
        "b71945eb-e9b7-4ea9-8c84-03cc47714232", "Krishna",
        None,
        "Country Head", None, "krishna@empireoe.com", None,
        None, ["Lithuania"], None, None, None, None,
    ),
    (
        "93b0c827-fc53-484d-8e76-6a100a6fe296", "Mano",
        None,
        "Admin", None, "mano@empireoe.com", None,
        None, None, None, None, None, None,
    ),
    (
        "d3055591-a852-434b-89c9-d60b464b7f53", "pulling off",
        f"{STORAGE_BASE}/profile_1760447339313.png",
        "Country Head", 917727243788, "mrfunnyshorts55@gmail.com", None,
        None, None, None, None, None, None,
    ),
    (
        "0bad3787-e95f-49f9-b07f-634ec1e6e318", "Renu V Menon",
        f"{STORAGE_BASE}/profile_1762852443229.png",
        "supend", 919633004738, "renu@empireoe.com", "918031495054",
        None, None, None, None, None, None,
    ),
    (
        "f8ba170e-283c-45a1-8ebe-286abe23eb0b", "Sharon ",
        f"{STORAGE_BASE}/profile_1757568643840.png",
        "Admin", 8129130745, "sharon@empireoe.com", "918129130745",
        "Kochi, kerala", None, None, None, None, None,
    ),
    (
        "4fb62a56-3955-48ae-9bf6-8dd0159a631c", "Shybin Biju",
        f"{STORAGE_BASE}/profile_1762852205416.png",
        "Lead manager", 917012304094, "shybin@empireoe.com", "918069637150",
        None, None, None, None, None, None,
    ),
    (
        "cbcf5f6d-497c-4d4d-8bdd-7f9412896760", "Sreekuttan Empire",
        f"{STORAGE_BASE}/profile_1763528833245.png",
        "Counsellor", 919778520897, "sreekuttan@empireoe.com", "918031495053",
        "Ernakulam", None, None, None, None, None,
    ),
    (
        "4e9afa2a-adf0-4cb7-9439-32f5c443db7e", "Timy",
        None,
        "Country Head", None, "timy@empireoe.com", None,
        None, ["Malta"], None, None, None, None,
    ),
    (
        "7453588a-f97c-4f8a-bc53-22804db99025", "Tisna Antony",
        None,
        "suspend", 916282584644, "tizna@empireoe.com", "918031495054",
        None, None, None, None, None, None,
    ),
    (
        "c05d2b75-b75c-4116-bf1f-927b713bddd9", "Abel",
        f"{STORAGE_BASE}/profile_1763443682954.png",
        "Admin", 917356533368, "web@empireoe.com", None,
        None, None, None, None, None, None,
    ),
    (
        "7c51c913-0a58-4efc-bbf6-2e95a64b6e6f", "Sharon Rodrigues",
        f"{STORAGE_BASE}/profile_1767752939400.png",
        "Admin", 8129130745, None, None,
        None, ["Latvia"], None, None, None, None,
    ),
    (
        "626e8a20-5f54-4f8f-98f9-4d9a1a7b7a9c", "Laimy Gracy Thomas",
        f"{STORAGE_BASE}/profile_1762408772050.png",
        "Admin", 9778418067, None, None,
        None, None, None, None, None, None,
    ),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def seed():
    print("=" * 60)
    print("Empireo Backend — Local Seed Script")
    print("=" * 60)

    session = sync_session_factory()

    try:
        # ---------------------------------------------------------------
        # 1. Clear existing seed data (FK-safe order)
        #    Don't delete eb_users or profiles — they may have FK refs
        #    from imported data (eb_students, leadslist, attendance)
        # ---------------------------------------------------------------
        print("\n[1/7] Clearing existing seed data ...")
        _run(session, "DELETE eb_user_roles", "DELETE FROM eb_user_roles")
        _run(session, "DELETE eb_role_permissions", "DELETE FROM eb_role_permissions")
        _run(session, "DELETE eb_refresh_tokens", "DELETE FROM eb_refresh_tokens")
        _run(session, "DELETE eb_roles", "DELETE FROM eb_roles")
        _run(session, "DELETE eb_permissions", "DELETE FROM eb_permissions")

        # ---------------------------------------------------------------
        # 2. Insert roles
        # ---------------------------------------------------------------
        print("\n[2/7] Inserting eb_roles ...")
        for rid, name, desc in ROLES:
            _run(
                session,
                f"role: {name}",
                """
                INSERT INTO eb_roles (id, name, description)
                VALUES (:id, :name, :desc)
                ON CONFLICT (id) DO NOTHING
                """,
                {"id": rid, "name": name, "desc": desc},
            )

        # ---------------------------------------------------------------
        # 3. Insert permissions
        # ---------------------------------------------------------------
        print("\n[3/7] Inserting eb_permissions ...")
        for pid, resource, action in PERMISSIONS:
            _run(
                session,
                f"perm: {resource}:{action}",
                """
                INSERT INTO eb_permissions (id, resource, action)
                VALUES (:id, :resource, :action)
                ON CONFLICT (id) DO NOTHING
                """,
                {"id": pid, "resource": resource, "action": action},
            )

        # ---------------------------------------------------------------
        # 4. Insert users
        # ---------------------------------------------------------------
        print("\n[4/7] Inserting eb_users ...")
        for uid, email, name, dept, active, legacy, phone, caller, loc, countries in USERS:
            _run(
                session,
                f"user: {email}",
                """
                INSERT INTO eb_users (id, email, full_name, hashed_password, department,
                                      is_active, legacy_supabase_id, phone, caller_id,
                                      location, countries, created_at, updated_at)
                VALUES (:id, :email, :full_name, :hashed_password, :department,
                        :is_active, :legacy_supabase_id, :phone, :caller_id,
                        :location, CAST(:countries AS jsonb), NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET
                    hashed_password = EXCLUDED.hashed_password,
                    is_active = EXCLUDED.is_active,
                    legacy_supabase_id = EXCLUDED.legacy_supabase_id,
                    updated_at = NOW()
                """,
                {
                    "id": uid,
                    "email": email,
                    "full_name": name,
                    "hashed_password": HASHED_PW,
                    "department": dept,
                    "is_active": active,
                    "legacy_supabase_id": legacy,
                    "phone": phone,
                    "caller_id": caller,
                    "location": loc,
                    "countries": countries,
                },
            )

        # ---------------------------------------------------------------
        # 5. Insert user-role mappings
        # ---------------------------------------------------------------
        print("\n[5/7] Inserting eb_user_roles ...")
        for uid, rid in USER_ROLES:
            _run(
                session,
                f"user_role: {uid[:8]}... -> {rid[:8]}...",
                """
                INSERT INTO eb_user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                ON CONFLICT (user_id, role_id) DO NOTHING
                """,
                {"user_id": uid, "role_id": rid},
            )

        # ---------------------------------------------------------------
        # 6. Insert role-permission mappings
        # ---------------------------------------------------------------
        print(f"\n[6/7] Inserting eb_role_permissions ({len(ROLE_PERMISSIONS)} rows) ...")
        for role_id, perm_id in ROLE_PERMISSIONS:
            session.execute(
                text("""
                    INSERT INTO eb_role_permissions (role_id, permission_id)
                    VALUES (:role_id, :permission_id)
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                """),
                {"role_id": role_id, "permission_id": perm_id},
            )
        session.commit()
        print(f"  -> Inserted {len(ROLE_PERMISSIONS)} role-permission mappings ... OK")

        # ---------------------------------------------------------------
        # 7. Insert profiles
        # ---------------------------------------------------------------
        print("\n[7/7] Inserting profiles ...")
        for (
            pid, diplay_name, profilepicture, designation, phone, email,
            caller_id, location, countries, user_type, freelancer_status,
            fcm_token, user_id
        ) in PROFILES:
            # Build the countries literal for Postgres TEXT[]
            if countries:
                countries_literal = "{" + ",".join(f'"{c}"' for c in countries) + "}"
            else:
                countries_literal = None

            try:
                _run(
                    session,
                    f"profile: {diplay_name}",
                    """
                    INSERT INTO profiles (id, diplay_name, profilepicture, designation, phone,
                                          email, "callerId", location, countries, user_type,
                                          freelancer_status, fcm_token, user_id)
                    VALUES (:id, :diplay_name, :profilepicture, :designation, :phone,
                            :email, :caller_id, :location, CAST(:countries AS text[]), :user_type,
                            :freelancer_status, :fcm_token, :user_id)
                    ON CONFLICT (id) DO UPDATE SET
                        diplay_name = EXCLUDED.diplay_name,
                        designation = EXCLUDED.designation,
                        profilepicture = COALESCE(EXCLUDED.profilepicture, profiles.profilepicture)
                    """,
                    {
                        "id": pid,
                        "diplay_name": diplay_name,
                        "profilepicture": profilepicture,
                        "designation": designation,
                        "phone": phone,
                        "email": email,
                        "caller_id": caller_id,
                        "location": location,
                        "countries": countries_literal,
                        "user_type": user_type,
                        "freelancer_status": freelancer_status,
                        "fcm_token": fcm_token,
                        "user_id": user_id,
                    },
                )
            except Exception as e:
                session.rollback()
                print(f"SKIPPED (duplicate constraint: {e.__class__.__name__})")

        # ---------------------------------------------------------------
        # Done
        # ---------------------------------------------------------------
        print("\n" + "=" * 60)
        print("Seed complete!")
        print(f"  Roles:            {len(ROLES)}")
        print(f"  Permissions:      {len(PERMISSIONS)}")
        print(f"  Users:            {len(USERS)}")
        print(f"  User-Roles:       {len(USER_ROLES)}")
        print(f"  Role-Permissions: {len(ROLE_PERMISSIONS)}")
        print(f"  Profiles:         {len(PROFILES)}")
        print(f"  Password:         Empire@2025 (all users)")
        print("=" * 60)

    except Exception as exc:
        session.rollback()
        print(f"\n\nERROR: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
