import asyncio
import contextlib
import json
import logging
from typing import Awaitable, Callable

from aio_pika import Message, connect
from aio_pika.abc import AbstractConnection, AbstractIncomingMessage

from src.config.config import Config

LOGGER = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def get_broker_connection(config: Config):
    connection = await connect(config.rabbitmq_url)
    async with connection:
        LOGGER.info("Opening connection with RabbitMQ")
        yield connection
        LOGGER.info("Closing connection with RabbitMQ")


async def poll_consuming(
    connection: AbstractConnection,
    queue_name: str,
    process_message_callback: Callable[[dict], Awaitable[None]],
) -> None:
    async def on_message(message: AbstractIncomingMessage) -> None:
        LOGGER.debug("Received message %r" % message)
        try:
            await process_message_callback(json.loads(message.body.decode()))
            await message.ack()
        except Exception as e:
            LOGGER.error(f"Error occured while processing message {message}: {e}")
            await message.nack()

    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name)

    await queue.consume(on_message)

    LOGGER.info(f"Waiting for messages in queue {queue}")
    await asyncio.Future()


async def publish_message(
    connection: AbstractConnection, queue_name: str, message: dict
):
    channel = await connection.channel()

    queue = await channel.declare_queue(queue_name)

    await channel.default_exchange.publish(
        Message(json.dumps(message).encode()), routing_key=queue.name
    )
    LOGGER.info(f"Publish message {message}, to queue {queue_name}")
