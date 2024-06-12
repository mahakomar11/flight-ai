import json
import logging
from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel

from src.config.config import get_config


def get_channel(queues: list[str] = None) -> BlockingChannel:
    config = get_config()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=config.rabbitmq_host,
            port=config.rabbitmq_port_main,
            credentials=pika.PlainCredentials(
                username=config.rabbitmq_user, password=config.rabbitmq_pass
            ),
        )
    )
    channel = connection.channel()
    for queue in queues:
        channel.queue_declare(queue=queue)

    return channel


def poll_consuming(queue: str, on_message_callback: Callable):
    channel = get_channel([queue])
    channel.basic_consume(
        queue=queue, on_message_callback=on_message_callback, auto_ack=True
    )

    logging.info("Started RabbitMQ listener...")
    channel.start_consuming()


def publish_message(queue: str, data: dict):
    channel = get_channel([queue])
    try:
        channel.basic_publish(
            exchange="", routing_key="requests_queue", body=json.dumps(data)
        )
    finally:
        channel.close()
