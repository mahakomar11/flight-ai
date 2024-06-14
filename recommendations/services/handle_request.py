import logging

from recommendations.requesters.requesters import (
    get_flight_requester,
    get_openai_requester,
)
from recommendations.services.generate_recommendation import GenerationService
from recommendations.services.get_flight import GetFlightService
from src.config.config import get_config
from src.infrastructure.broker.constants import RESPONSES_QUEUE_NAME
from src.infrastructure.broker.rabbit import publish_message
from src.infrastructure.database.repositories.recommendation import (
    RecommendationRepository,
)
from src.infrastructure.database.repositories.user import UserRepository
from src.infrastructure.database.session import get_session
from src.schemas.recommendation import Recommendation


async def handle_user_request(user_id: int, flight_number: str, flight_date: str):
    config = get_config()

    # handle flight
    flight = await GetFlightService(get_flight_requester(config)).get_flight(
        flight_number, departure_date_time=flight_date
    )
    if flight is None:
        publish_message(
            RESPONSES_QUEUE_NAME,
            {
                "user_id": user_id,
                "message": "Cannot find your flight, perhaps wrong flight number?😔 Please, try /flight again",
            },
        )
        return

    # handle generation
    async with get_session(config) as session:
        user = await UserRepository(session).get(user_id)

    generation_service = GenerationService(get_openai_requester(config))
    (
        initial_recommendation,
        recommendations_per_day,
    ) = await generation_service.generate_recommendations(
        user_answers=user.answers, flight=flight
    )
    logging.info(f"Got recommendations for user {user_id}")

    # Send first recommendation
    publish_message(
        RESPONSES_QUEUE_NAME, {"user_id": user_id, "message": initial_recommendation}
    )

    # Save recommendations for later
    recommendations = []
    for date, rec in recommendations_per_day.items():
        recommendations.append(
            Recommendation(user_id=user_id, scheduled_at=date, message=rec)
        )
    async with get_session(config) as session:
        recommendation_repository = RecommendationRepository(session)
        await recommendation_repository.post_many(recommendations)
