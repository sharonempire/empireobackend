from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.modules.users.models import User, Role
from app.modules.users.schemas import UserCreate, UserUpdate
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, ConflictError


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User:
        result = await self.db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_users(self, page: int = 1, size: int = 20, department: str | None = None):
        q = select(User).options(selectinload(User.roles))
        if department:
            q = q.where(User.department == department)
        total_q = select(func.count()).select_from(q.subquery())
        total = (await self.db.execute(total_q)).scalar()
        q = q.offset((page - 1) * size).limit(size).order_by(User.created_at.desc())
        result = await self.db.execute(q)
        return result.scalars().all(), total

    async def create_user(self, data: UserCreate) -> User:
        existing = await self.get_by_email(data.email)
        if existing:
            raise ConflictError(f"User with email {data.email} already exists")
        user = User(
            email=data.email,
            phone=data.phone,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            department=data.department,
        )
        for role_name in data.role_names:
            role = (await self.db.execute(select(Role).where(Role.name == role_name))).scalar_one_or_none()
            if role:
                user.roles.append(role)
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        user = await self.get_by_id(user_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.db.flush()
        return user

    async def assign_roles(self, user_id: UUID, role_names: list[str]) -> User:
        user = await self.get_by_id(user_id)
        user.roles.clear()
        for name in role_names:
            role = (await self.db.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
            if role:
                user.roles.append(role)
        await self.db.flush()
        return user
