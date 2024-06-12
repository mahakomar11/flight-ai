from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import User as UserORM
from src.schemas.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(UserORM).where(UserORM.id == user_id)
        )
        user_orm: UserORM | None = result.scalars().one_or_none()
        if user_orm is None:
            return None
        return User.model_validate(user_orm)

    async def post(self, user: User) -> None:
        await self._session.execute(insert(UserORM), user.model_dump())
