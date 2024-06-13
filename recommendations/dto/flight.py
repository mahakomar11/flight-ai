from datetime import datetime

from pydantic import BaseModel


class FlightPoint(BaseModel):
    airport: str
    datetime: datetime


class Flight(BaseModel):
    departure: FlightPoint
    arrival: FlightPoint
