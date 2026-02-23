from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.users.models import User, UserRole
from app.modules.users.schemas import UserCreate, UserUpdate


async def list_users(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    department: str | None = None,
) -> tuple[list[User], int]:
    stmt = select(User).options(selectinload(User.user_roles).selectinload(UserRole.role))
    count_stmt = select(func.count()).select_from(User)

    if department:
        stmt = stmt.where(User.department == department)
        count_stmt = count_stmt.where(User.department == department)

    total = (await db.execute(count_stmt)).scalar()
    stmt = stmt.offset((page - 1) * size).limit(size).order_by(User.full_name)
    result = await db.execute(stmt)
    return result.scalars().all(), total


async def get_user(db: AsyncSession, user_id: UUID) -> User:
    stmt = (
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    return user


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictError("Email already registered")

    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        phone=data.phone,
        department=data.department,
        caller_id=data.caller_id,
        location=data.location,
        countries=data.countries,
    )
    db.add(user)
    await db.flush()

    for role_id in data.role_ids:
        db.add(UserRole(user_id=user.id, role_id=role_id))

    await db.flush()
    return await get_user(db, user.id)


async def update_user(db: AsyncSession, user_id: UUID, data: UserUpdate) -> User:
    user = await get_user(db, user_id)
    update_data = data.model_dump(exclude_unset=True)
    role_ids = update_data.pop("role_ids", None)

    for key, value in update_data.items():
        setattr(user, key, value)

    if role_ids is not None:
        # Remove old roles
        for ur in list(user.user_roles):
            await db.delete(ur)
        await db.flush()
        # Add new roles
        for role_id in role_ids:
            db.add(UserRole(user_id=user.id, role_id=role_id))

    await db.flush()
    return await get_user(db, user_id)
