import asyncio
import logging
from datetime import datetime

from src.config.config import get_config
from src.infrastructure.broker.constants import RESPONSES_QUEUE_NAME
from src.infrastructure.broker.rabbit import get_broker_connection, publish_message
from src.infrastructure.database.repositories.recommendation import (
    RecommendationRepository,
)
from src.infrastructure.database.session import get_session
from src.schemas.exchange_messages import ResponseMessage

PERIOD_SECS = 3600 * 5

LOGGER = logging.getLogger(__name__)


async def notify_user(config):
    LOGGER.info("Looking for scheduled recommendations")
    now = datetime.now()

    async with get_session(config) as session:
        recommendation_repository = RecommendationRepository(session)
        actual_recommendations = await recommendation_repository.filter_by_date(now)

    LOGGER.info(f"Found {len(actual_recommendations)} recommendations for today")
    async with get_broker_connection(config) as connection:
        for rec in actual_recommendations:
            LOGGER.debug(f"Sending to user {rec.user_id} notification")
            await publish_message(
                connection,
                RESPONSES_QUEUE_NAME,
                ResponseMessage(user_id=rec.user_id, message=rec.message).model_dump(),
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
