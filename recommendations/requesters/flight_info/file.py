import json

from recommendations.requesters.flight_info.base import FlightInfoBase
from recommendations.requesters.flight_info.schemas import FlightInfoResponse


class FlightInfoJson(FlightInfoBase):
    def __init__(self, path: str, api_key: str = ""):
        self.json_file_path = path

    async def get_flight_info(
        self, carrier_code: str, flight_number: str, departure_date_time: str
    ) -> FlightInfoResponse:
        with open(self.json_file_path) as f:
            data = json.load(f)

        flight_key = f"{carrier_code} {flight_number} {departure_date_time}"
        if flight_key not in data:
            return FlightInfoResponse(data=[])

        return FlightInfoResponse(**data[flight_key])
