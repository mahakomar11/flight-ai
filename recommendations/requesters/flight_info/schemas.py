from datetime import date, time

from pydantic import BaseModel, Extra


class FlightInfoAirport(BaseModel):
    iata: str

    class Config:
        extra = Extra.ignore


class FlightInfoDate(BaseModel):
    local: date
    utc: date


class FlightInfoTime(BaseModel):
    local: time
    utc: time


class FlightInfoWaypoint(BaseModel):
    airport: FlightInfoAirport
    date: FlightInfoDate
    time: FlightInfoTime


class FlightInfoData(BaseModel):
    departure: FlightInfoWaypoint
    arrival: FlightInfoWaypoint

    class Config:
        extra = Extra.ignore


class FlightInfoResponse(BaseModel):
    data: list[FlightInfoData]

    class Config:
        extra = Extra.ignore
