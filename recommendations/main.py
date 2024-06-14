import asyncio
import logging
import sys

from recommendations.notifier.notifier import PERIOD_SECS, check_notifications
from recommendations.services.handle_request import handle_user_request
from src.config.config import get_config
from src.infrastructure.broker.constants import REQUESTS_QUEUE_NAME
from src.infrastructure.broker.rabbit import get_broker_connection, poll_consuming
from src.schemas.exchange_messages import RequestMessage


async def consume_requests():
    config = get_config()

    async with get_broker_connection(config) as connection:

        async def process_request(exchange_message: dict):
            await handle_user_request(connection, RequestMessage(**exchange_message))

        await poll_consuming(
            connection,
            queue_name=REQUESTS_QUEUE_NAME,
            process_message_callback=process_request,
        )


async def main() -> None:
    await asyncio.gather(check_notifications(PERIOD_SECS), consume_requests())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
