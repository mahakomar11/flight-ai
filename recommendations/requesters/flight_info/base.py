import abc

from recommendations.requesters.flight_info.schemas import FlightInfoResponse


class FlightInfoBase(abc.ABC):
    @abc.abstractmethod
    def __init__(self, path: str, api_key: str):
        pass

    @abc.abstractmethod
    async def get_flight_info(
        self, carrier_code: str, flight_number: str, departure_date_time: str
    ) -> FlightInfoResponse:
        pass
