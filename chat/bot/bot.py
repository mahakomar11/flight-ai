import logging.config

from chat.constants.texts import (
    AUTH_TEXT_FOR_KNOWN,
    AUTH_TEXT_FOR_UNKNOWN,
    FLIGHT_DATE_QUESTION,
    FLIGHT_NUMBER_QUESTION,
    FLIGHT_TEXT_FOR_UNKNOWN,
    GREETING_TEXT_FOR_KNOWN,
    GREETING_TEXT_FOR_UNKNOWN,
)
from chat.helpers.user_form import get_user_answers
from src.config.config import Config
from src.infrastructure.broker.constants import REQUESTS_QUEUE_NAME
from src.infrastructure.broker.rabbit import get_broker_connection, publish_message
from src.infrastructure.database.repositories.user import UserRepository
from src.infrastructure.database.session import get_session
from src.schemas.exchange_messages import RequestMessage
from src.schemas.user import User

LOGGER = logging.getLogger(__name__)


class FlightAIBot:
    def __init__(self, config: Config):
        self.config = config

    async def _is_user_exists(self, user_id: int) -> bool:
        async with get_session(self.config) as session:
            LOGGER.debug(f"Getting user with id {user_id}")
            user = await UserRepository(session).get(user_id=user_id)
            LOGGER.debug(f"Got user {user}")

        return user is not None

    async def start(self, user_id: int) -> str:
        if await self._is_user_exists(user_id):
            return GREETING_TEXT_FOR_KNOWN

        return GREETING_TEXT_FOR_UNKNOWN

    async def approve_auth(self, user_id: int, user_phone: str = "mock") -> str:
        if await self._is_user_exists(user_id):
            return AUTH_TEXT_FOR_KNOWN

        user_answers = get_user_answers(user_phone)
        user = User(id=user_id, phone="mock", answers=user_answers)
        async with get_session(self.config) as session:
            await UserRepository(session).post(user)
        return AUTH_TEXT_FOR_UNKNOWN

    async def ask_flight_number(self, user_id: int) -> str:
        if await self._is_user_exists(user_id):
            return FLIGHT_NUMBER_QUESTION

        return FLIGHT_TEXT_FOR_UNKNOWN

    async def ask_flight_date(self) -> str:
        return FLIGHT_DATE_QUESTION

    async def process_flight_data(self, request_message: RequestMessage):
        LOGGER.warning(f"Publishing to queue {request_message}")
        async with get_broker_connection(self.config) as connection:
            await publish_message(
                connection, REQUESTS_QUEUE_NAME, request_message.model_dump()
            )

        return (
            f"Great! Your flight number is {request_message.flight_number} and flight date is {request_message.flight_date}. "
            f"I am preparing recommendations for you."
        )
