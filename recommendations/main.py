import asyncio
import json
import logging
import sys
import threading

from recommendations.notifier.notifier import PERIOD_SECS, check_notifications
from recommendations.services.handle_request import handle_user_request
from src.infrastructure.broker.constants import REQUESTS_QUEUE_NAME
from src.infrastructure.broker.rabbit import poll_consuming


def consume_requests(loop: asyncio.AbstractEventLoop):
    def on_message(channel, method, properties, body):
        message = json.loads(body)

        user_id = message["user_id"]
        flight_number = message["flight_number"]
        flight_date = message["flight_date"]

        logging.warning(f"Got message {message}")

        asyncio.run_coroutine_threadsafe(
            handle_user_request(user_id, flight_number, flight_date), loop
        )

        channel.basic_ack(method.delivery_tag)

    poll_consuming(REQUESTS_QUEUE_NAME, on_message_callback=on_message)


async def main() -> None:
    requests_consumer_thread = threading.Thread(
        target=consume_requests, args=(asyncio.get_event_loop(),), daemon=True
    )
    requests_consumer_thread.start()

    await check_notifications(PERIOD_SECS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
