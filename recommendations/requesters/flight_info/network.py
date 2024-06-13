import httpx

from recommendations.requesters.flight_info.base import FlightInfoBase
from recommendations.requesters.flight_info.schemas import FlightInfoResponse


class FlightInfoAPI(FlightInfoBase):
    GET_SCHEDULE_ENDPOINT = "/schedules"

    def __init__(self, path: str, api_key: str):
        self.base_url = f"https://{path}"
        self.headers = self._create_headers(path, api_key)

    async def get_flight_info(
        self, carrier_code: str, flight_number: str, departure_date_time: str
    ) -> FlightInfoResponse:
        params = {
            "version": "v2",
            "CarrierCode": carrier_code,
            "FlightNumber": flight_number,
            "DepartureDateTime": departure_date_time,
            "CodeType": "IATA",
        }
        response = await self._make_request(self.GET_SCHEDULE_ENDPOINT, params)
        return FlightInfoResponse(**response)

    async def _make_request(
        self, endpoint: str, params: dict[str, str]
    ) -> dict[str, str]:
        url = self.base_url + endpoint

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _create_headers(host: str, api_key: str):
        return {"X-Rapidapi-Key": api_key, "X-Rapidapi-Host": host}
