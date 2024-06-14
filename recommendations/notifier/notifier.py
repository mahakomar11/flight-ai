import asyncio
import logging
from datetime import datetime

from src.config.config import get_config
from src.infrastructure.broker.constants import RESPONSES_QUEUE_NAME
from src.infrastructure.broker.rabbit import publish_message
from src.infrastructure.database.repositories.recommendation import (
    RecommendationRepository,
)
from src.infrastructure.database.session import get_session

PERIOD_SECS = 3600 * 5


async def notify_user(config):
    logging.debug("Looking for scheduled recommendations")
    now = datetime.now()

    async with get_session(config) as session:
        recommendation_repository = RecommendationRepository(session)
        actual_recommendations = await recommendation_repository.filter_by_date(now)

    logging.info(f"Found {len(actual_recommendations)} recommendations for today")
    for rec in actual_recommendations:
        logging.debug(f"Sending to user {rec.user_id} message")
        publish_message(
            RESPONSES_QUEUE_NAME, {"user_id": rec.user_id, "message": rec.message}
        )
        async with get_session(config) as session:
            recommendation_repository = RecommendationRepository(session)
            await recommendation_repository.mark_as_delivered(rec.id)


async def check_notifications(period_secs: int):
    config = get_config()

    while True:
        await notify_user(config)
        await asyncio.sleep(period_secs)


if __name__ == "__main__":
    asyncio.run(check_notifications(PERIOD_SECS))
