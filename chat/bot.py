import asyncio
import json
import logging
import sys
import threading

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

from chat.constants.texts import (
    AUTH_TEXT,
    FLIGHT_DATE_QUESTION,
    FLIGHT_NUMBER_QUESTION,
    GREETING_TEXT_FOR_KNOWN,
    GREETING_TEXT_FOR_UNKNOWN,
)
from helpers.user_form import get_user_answers
from src.config.config import get_config
from src.infrastructure.broker.constants import (
    REQUESTS_QUEUE_NAME,
    RESPONSES_QUEUE_NAME,
)
from src.infrastructure.broker.rabbit import poll_consuming, publish_message
from src.infrastructure.database.repositories.user import UserRepository
from src.infrastructure.database.session import get_session
from src.schemas.user import User

config = get_config()
bot = Bot(
    token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

form_router = Router()


class Form(StatesGroup):
    flight_number = State()
    flight_date = State()


@dp.message(CommandStart())
async def command_start(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    logging.debug(f"Got /start command from user {message.chat.id}")
    async with get_session(config) as session:
        logging.debug(f"Getting user with id {message.chat.id}")
        user = await UserRepository(session).get(user_id=message.chat.id)
        logging.debug(f"Got user {user}")

    if user is None:
        await message.answer(GREETING_TEXT_FOR_UNKNOWN)
    else:
        await message.answer(GREETING_TEXT_FOR_KNOWN)


@dp.message(Command("filled"))
async def command_filled(message: Message) -> None:
    """
    This handler receives messages with `/filled` command
    """
    logging.warning(f"Getting form data for user {message.chat.id}")
    user_answers = get_user_answers("mock")  # TODO: change to phone
    user = User(id=message.chat.id, phone="mock", answers=user_answers)
    async with get_session(config) as session:
        await UserRepository(session).post(user)
    await message.answer(AUTH_TEXT)


@form_router.message(Command("flight"))
async def command_flight(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.flight_number)
    await message.answer(FLIGHT_NUMBER_QUESTION, reply_markup=ReplyKeyboardRemove())


@form_router.message(Form.flight_number)
async def process_flight_number(message: Message, state: FSMContext) -> None:
    await state.update_data(flight_number=message.text)
    await state.set_state(Form.flight_date)
    await message.answer(FLIGHT_DATE_QUESTION, reply_markup=ReplyKeyboardRemove())


@form_router.message(Form.flight_date)
async def process_flight_date(message: Message, state: FSMContext) -> None:
    data = await state.update_data(flight_date=message.text)
    await state.clear()
    await message.answer(
        f"Great! Your flight number is {data['flight_number']} and flight date is {data['flight_date']}. "
        f"We are preparing recommendations for you."
    )
    data["user_id"] = message.chat.id
    logging.warning(f"Publishing to queue {data}")
    publish_message(REQUESTS_QUEUE_NAME, data)


def consume_responses(loop: asyncio.BaseEventLoop):
    def on_message_callback(channel, method, properties, body):
        message = json.loads(body)

        user_id = message["user_id"]
        message_text = message["message"]

        logging.warning(f"Got message {message} for user {user_id}")
        # Send the message to the specified user_id
        asyncio.run_coroutine_threadsafe(send_message(user_id, message_text), loop)

        channel.basic_ack(method.delivery_tag)

    poll_consuming(RESPONSES_QUEUE_NAME, on_message_callback)


async def send_message(user_id: int, message_text: str):
    try:
        await bot.send_message(
            user_id, message_text.replace("**", "*"), parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logging.error(f"Error sending message to {user_id}: {e}")


async def main() -> None:
    dp.include_router(form_router)

    responses_consumer_thread = threading.Thread(
        target=consume_responses, args=(asyncio.get_event_loop(),), daemon=True
    )
    responses_consumer_thread.start()

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
