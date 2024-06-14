from recommendations.requesters.flight_info.base import FlightInfoBase
from recommendations.requesters.flight_info.file import FlightInfoJson
from recommendations.requesters.flight_info.network import FlightInfoAPI
from recommendations.requesters.openai.network import OpenAIClient
from src.config.config import Config


def get_flight_requester(config: Config) -> FlightInfoBase:
    if config.flight_api_mock:
        return FlightInfoJson(path=config.flight_api_path)
    return FlightInfoAPI(path=config.flight_api_path, api_key=config.flight_api_key)


def get_openai_requester(config: Config) -> OpenAIClient:
    return OpenAIClient(config.open_ai_path, config.open_ai_key)
