from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import Recommendation as RecommendationORM
from src.schemas.recommendation import Recommendation


class RecommendationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, recommendation_id: str) -> Recommendation | None:
        result = await self._session.execute(
            select(RecommendationORM).where(RecommendationORM.id == recommendation_id)
        )
        recommendation_orm: RecommendationORM | None = result.scalars().one_or_none()
        if recommendation_orm is None:
            return None
        return Recommendation.model_validate(recommendation_orm)

    async def post(self, recommendation: Recommendation) -> None:
        await self._session.execute(
            insert(RecommendationORM), recommendation.model_dump()
        )

    async def post_many(self, recommendations: list[Recommendation]) -> None:
        await self._session.execute(
            insert(RecommendationORM).values(
                [rec.model_dump() for rec in recommendations]
            )
        )

    async def filter_by_date(self, date: datetime) -> list[Recommendation]:
        result = await self._session.execute(
            select(RecommendationORM)
            .where(RecommendationORM.scheduled_at == date)
            .where(RecommendationORM.delivered is False)
        )
        recommendations_orm = result.scalars().all()
        return [
            Recommendation.model_validate(rec_orm) for rec_orm in recommendations_orm
        ]

    async def mark_as_delivered(self, recommendation_id: str):
        await self._session.execute(
            update(RecommendationORM)
            .where(RecommendationORM.id == recommendation_id)
            .values(delivered=True)
        )
