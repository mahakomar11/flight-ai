import logging
from datetime import datetime, timedelta

from recommendations.dto.flight import Flight
from recommendations.requesters.openai.network import OpenAIClient

LOGGER = logging.getLogger(__name__)


class GenerationService:
    RELATIVE_DAYS = [-2, -1, 0, 1, 2]
    INITIAL_CONCLUSION = (
        "**You don't need to remember it, I'll send you notifications for each day**🤗"
    )
    DAILY_INTRO = "Hi! Here is your recommendations for today😊"

    def __init__(self, openai_client: OpenAIClient, model: str = "gpt-4o-2024-05-13"):
        self.openai_client = openai_client
        self.model = model

    async def generate_recommendations(
        self, user_answers: dict[str, str], flight: Flight
    ) -> tuple[str, dict]:
        system_message = (
            "You are an expert in designing personalized, science-backed sleep and circadian protocols. "
            "Your goal is to create a detailed, tailored plan that addresses an individual's chronotype and preferences, "
            "with the aim of enhancing their sleep quality and daytime alertness for dealing with jet lag because of flight. "
            "Your recommendations should be actionable, time-specific and based on flight departure and arrival times and time zone differences."
        )

        user_message = (
            "Based on the provided circadian assessment (user's personal assessment), "
            "generate flight recommendations for 2 days before flight and 2 days after flight that are targeting melatonin, caffeine, "
            "physical activity, light exposure, sleep onset and offset timing. "
            f"User's answer to questions: {self.flatten_user_answers(user_answers)} "
            f"User is going to flight from airport {flight.departure.airport} (departure local time {flight.departure.datetime}) to {flight.arrival.airport} "
            f"(arrival local time {flight.arrival.datetime})."
        )

        message_template = (
            "[Greeting]\n"
            "[Introduction]\n"
            "---\n"
            "☀**[date of day -2]**\n"
            "[recommendations for day -2]\n"
            "---\n"
            "☀**[date of day -1]**\n"
            "[recommendations for day -1]\n"
            "---\n"
            "☀**[date of flight day]**\n"
            "[recommendations for flight day]\n"
            "---\n"
            "☀**[date of day +1]**\n"
            "[recommendations for day +1]\n"
            "---\n"
            "☀**[date of day +2]**\n"
            "[recommendations for day +2]\n"
            "---\n"
            "[Conclusion]"
        )

        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": user_message
                + "\nWrite message to the user. Don't use signature. Use the following template.\n"
                + message_template,
            },
        ]

        recommendation_parts = []
        while (
            len(recommendation_parts) != len(self.RELATIVE_DAYS) + 2
        ):  # Check for the format
            LOGGER.warning(
                f"Try again ask the model, now {len(recommendation_parts)} parts of recommendation gotten"
            )
            raw_recommendation = await self.openai_client.create_chat_completion(
                messages, model=self.model
            )
            recommendation_parts = raw_recommendation.split("---\n")

        recommendations_per_day = self._schedule_recommendations(
            flight.departure.datetime, recommendation_parts[1:-1]
        )

        return (
            self._get_initial_recommendation(raw_recommendation),
            recommendations_per_day,
        )

    def _get_initial_recommendation(self, recommendation: str) -> str:
        return "\n\n".join(
            [recommendation.replace("---\n", ""), self.INITIAL_CONCLUSION]
        )

    def _schedule_recommendations(
        self, flight_date: datetime, recommendations_for_days: list[str]
    ):
        recommendations_per_day = dict()
        for relative_day, rec_part in zip(self.RELATIVE_DAYS, recommendations_for_days):
            recommendations_per_day[
                self.get_scheduled_at(flight_date, relative_day=relative_day)
            ] = "\n\n".join([self.DAILY_INTRO, rec_part])
        return recommendations_per_day

    @staticmethod
    def flatten_user_answers(user_answers: dict[str, str]) -> str:
        return " ".join([f"{key} {value}" for key, value in user_answers.items()])

    @staticmethod
    def get_scheduled_at(flight_date: datetime, relative_day: int) -> datetime:
        return flight_date + timedelta(days=relative_day) - timedelta(hours=5)
