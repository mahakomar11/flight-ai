import logging

from recommendations.services.generate_recommendation import GenerationService
from recommendations.services.get_flight import GetFlightService
from src.config.config import Config
from src.infrastructure.broker.constants import RESPONSES_QUEUE_NAME
from src.infrastructure.broker.rabbit import publish_message
from src.infrastructure.database.repositories.recommendation import (
    RecommendationRepository,
)
from src.infrastructure.database.repositories.user import UserRepository
from src.infrastructure.database.session import get_session
from src.schemas.exchange_messages import RequestMessage, ResponseMessage
from src.schemas.recommendation import Recommendation
from src.schemas.user import User

LOGGER = logging.getLogger(__name__)


class UserRequestsService:
    def __init__(
        self,
        config: Config,
        broker_connection,
        flight_service: GetFlightService,
        generation_service: GenerationService,
    ):
        self.config = config
        self.broker_connection = broker_connection
        self.flight_service = flight_service
        self.generation_service = generation_service

    async def process_request(self, exchange_message: dict):
        request = RequestMessage(**exchange_message)

        flight = await self.flight_service.get_flight(
            request.flight_number, departure_date_time=request.flight_date
        )
        if flight is None:
            await self._send_response(
                ResponseMessage(
                    user_id=request.user_id,
                    message="Cannot find your flight, perhaps wrong flight number?😔 Please, try /flight again",
                )
            )
            return

        # handle generation
        user = await self._get_user(request.user_id)

        (
            initial_rec,
            recs_per_day,
        ) = await self.generation_service.generate_recommendations(
            user_answers=user.answers, flight=flight
        )
        LOGGER.info(f"Got recommendations for user {request.user_id}")

        await self._send_response(
            ResponseMessage(user_id=request.user_id, message=initial_rec)
        )
        await self._post_scheduled_recommendations(request.user_id, recs_per_day)

    async def _get_user(self, user_id: int) -> User:
        async with get_session(self.config) as session:
            return await UserRepository(session).get(user_id)

    async def _send_response(self, response_message: ResponseMessage):
        await publish_message(
            self.broker_connection, RESPONSES_QUEUE_NAME, response_message.model_dump()
        )

    async def _post_scheduled_recommendations(
        self, user_id: int, recommendations_per_day: dict
    ):
        recommendations = []
        for date, rec in recommendations_per_day.items():
            recommendations.append(
                Recommendation(user_id=user_id, scheduled_at=date, message=rec)
            )
        async with get_session(self.config) as session:
            recommendation_repository = RecommendationRepository(session)
            await recommendation_repository.post_many(recommendations)
