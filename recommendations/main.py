import asyncio
import logging.config
import sys

from recommendations.notifier.notifier import PERIOD_SECS, check_notifications
from recommendations.requesters.requesters import (
    get_flight_requester,
    get_openai_requester,
)
from recommendations.services.generate_recommendation import GenerationService
from recommendations.services.get_flight import GetFlightService
from recommendations.services.user_requests import UserRequestsService
from src.config.config import get_config
from src.infrastructure.broker.constants import REQUESTS_QUEUE_NAME
from src.infrastructure.broker.rabbit import get_broker_connection, poll_consuming
from src.logger.logger import build_log_config

logging.config.dictConfig(build_log_config("DEBUG"))
LOGGER = logging.getLogger(__name__)


async def consume_requests():
    config = get_config()
    flight_service = GetFlightService(get_flight_requester(config))
    generation_service = GenerationService(get_openai_requester(config))

    async with get_broker_connection(config) as connection:
        user_requests_service = UserRequestsService(
            config,
            connection,
            flight_service=flight_service,
            generation_service=generation_service,
        )

        await poll_consuming(
            connection,
            queue_name=REQUESTS_QUEUE_NAME,
            process_message_callback=user_requests_service.process_request,
        )


async def main() -> None:
    await asyncio.gather(check_notifications(PERIOD_SECS), consume_requests())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
