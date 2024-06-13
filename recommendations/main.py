import asyncio
import json
import logging

from recommendations.requesters.flight_info.base import FlightInfoBase
from recommendations.requesters.flight_info.file import FlightInfoJson
from recommendations.requesters.flight_info.network import FlightInfoAPI
from recommendations.requesters.openai.network import OpenAIClient
from recommendations.services.get_flight import GetFlightService
from recommendations.services.get_recommendation import GetRecommendationService
from src.config.config import get_config
from src.infrastructure.broker.rabbit import publish_message
from src.infrastructure.database.repositories.recommendation import (
    RecommendationRepository,
)
from src.infrastructure.database.repositories.user import UserRepository
from src.infrastructure.database.session import get_session
from src.schemas.recommendation import Recommendation

RESPONSES_QUEUE_NAME = "responses_queue"


def get_flight_requester() -> FlightInfoBase:
    config = get_config()
    if config.flight_api_mock:
        return FlightInfoJson(path=config.flight_api_path)
    return FlightInfoAPI(path=config.flight_api_path, api_key=config.flight_api_key)


def on_message(channel, method, properties, body):
    message = json.loads(body)

    user_id = message["user_id"]
    flight_number = message["flight_number"]
    flight_date = message["flight_date"]

    logging.warning(f"Got message {message}")

    # Send the message to the specified user_id
    asyncio.run(generate_recommendations(user_id, flight_number, flight_date))


async def generate_recommendations(user_id: int, flight_number: str, flight_date: str):
    config = get_config()

    # handle flight
    flight = await GetFlightService(get_flight_requester()).get_flight(
        flight_number, departure_date_time=flight_date
    )
    if flight is None:
        publish_message(
            RESPONSES_QUEUE_NAME,
            {
                "user_id": user_id,
                "message": "Cannot find your flight, perhaps wrong flight number?:( Please, try /flight again",
            },
        )

    # handle generation
    async for session in get_session(config):
        user = await UserRepository(session).get(user_id)

    generation_service = GetRecommendationService(
        OpenAIClient(base_url=config.open_ai_path, api_key=config.open_ai_key)
    )
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
    async for session in get_session(config):
        recommendation_repository = RecommendationRepository(session)
        await recommendation_repository.post_many(recommendations)


asyncio.run(
    generate_recommendations(
        user_id=99649314, flight_number="G9508", flight_date="2024-06-14"
    )
)
