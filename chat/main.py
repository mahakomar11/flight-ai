import asyncio
import logging.config
import re

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

from chat.bot.bot import FlightAIBot
from chat.helpers.validate_date import is_valid_date
from src.config.config import get_config
from src.infrastructure.broker.constants import RESPONSES_QUEUE_NAME
from src.infrastructure.broker.rabbit import get_broker_connection, poll_consuming
from src.logger.logger import build_log_config
from src.schemas.exchange_messages import RequestMessage, ResponseMessage

logging.config.dictConfig(build_log_config("DEBUG"))
LOGGER = logging.getLogger(__name__)

config = get_config()

bot = Bot(
    token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
form_router = Router()
dp.include_router(form_router)

flightai_bot = FlightAIBot(config)


class Form(StatesGroup):
    flight_number = State()
    flight_date = State()


@dp.message(CommandStart())
async def command_start(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    LOGGER.debug(f"Got /start command from user {message.chat.id}")
    answer = await flightai_bot.start(message.chat.id)
    await message.answer(answer)


@dp.message(Command("filled"))
async def command_filled(message: Message) -> None:
    """
    This handler receives messages with `/filled` command
    """
    LOGGER.warning(f"Getting form data for user {message.chat.id}")
    answer = await flightai_bot.approve_auth(message.chat.id)
    await message.answer(answer)


@form_router.message(Command("flight"))
async def command_flight(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.flight_number)
    answer = await flightai_bot.ask_flight_number(message.chat.id)
    await message.answer(answer, reply_markup=ReplyKeyboardRemove())


@form_router.message(
    Form.flight_number,
    lambda message: re.match(
        r"^([a-zA-Z0-9]{2}[a-zA-Z]?)(\d{1,4}[a-zA-Z]?)$", message.text
    ),
)
async def process_flight_number(message: Message, state: FSMContext) -> None:
    await state.update_data(flight_number=message.text)
    await state.set_state(Form.flight_date)
    answer = await flightai_bot.ask_flight_date()
    await message.answer(answer, reply_markup=ReplyKeyboardRemove())


@form_router.message(
    Form.flight_number,
    lambda message: not re.match(
        r"^([a-zA-Z0-9]{2}[a-zA-Z]?)(\d{1,4}[a-zA-Z]?)$", message.text
    ),
)
async def process_wrong_flight_number(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.flight_number)
    answer = "Wrong number. Use IATA codes for flight number. It should be printed on your ticket."
    await message.answer(answer, reply_markup=ReplyKeyboardRemove())


@form_router.message(Form.flight_date, lambda message: is_valid_date(message.text))
async def process_flight_date(message: Message, state: FSMContext) -> None:
    data = await state.update_data(flight_date=message.text)
    await state.clear()
    data["user_id"] = message.chat.id
    answer = await flightai_bot.process_flight_data(RequestMessage(**data))
    await message.answer(answer)


@form_router.message(Form.flight_date, lambda message: not is_valid_date(message.text))
async def process_wrong_flight_date(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.flight_date)
    answer = "Wrong date. Use YYYY-MM-DD format for the flight date."
    await message.answer(answer, reply_markup=ReplyKeyboardRemove())


async def send_response(exchange_message: dict):
    response = ResponseMessage(**exchange_message)

    LOGGER.debug(f"Got message {response.message} for user {response.user_id}")

    try:
        await bot.send_message(
            response.user_id,
            response.message.replace("**", "*"),
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        LOGGER.error(f"Error sending message to {response.user_id}: {e}")


async def consume_responses():
    async with get_broker_connection(config) as connection:
        await poll_consuming(connection, RESPONSES_QUEUE_NAME, send_response)


async def main() -> None:
    await asyncio.gather(dp.start_polling(bot), consume_responses())


if __name__ == "__main__":
    LOGGER.debug("Starting chat application")
    asyncio.run(main())
