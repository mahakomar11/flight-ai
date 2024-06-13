from datetime import datetime

from recommendations.dto.flight import Flight, FlightPoint
from recommendations.requesters.flight_info.base import FlightInfoBase
from recommendations.requesters.flight_info.schemas import FlightInfoResponse
from src.helpers.flight_number import parse_iata_flight_number


class GetFlightService:
    def __init__(self, flight_requester: FlightInfoBase):
        self.flight_requester = flight_requester

    async def get_flight(
        self, iata_flight_number: str, departure_date_time: str
    ) -> Flight | None:
        iata_airline, flight_number = parse_iata_flight_number(iata_flight_number)
        flight_info: FlightInfoResponse = await self.flight_requester.get_flight_info(
            carrier_code=iata_airline,
            flight_number=flight_number,
            departure_date_time=departure_date_time,
        )
        if len(flight_info.data) == 0:
            return None

        return Flight(
            departure=FlightPoint(
                airport=flight_info.data[0].departure.airport.iata,
                datetime=datetime.combine(
                    flight_info.data[0].departure.date.local,
                    flight_info.data[0].departure.time.local,
                ),
            ),
            arrival=FlightPoint(
                airport=flight_info.data[0].arrival.airport.iata,
                datetime=datetime.combine(
                    flight_info.data[0].arrival.date.local,
                    flight_info.data[0].arrival.time.local,
                ),
            ),
        )
