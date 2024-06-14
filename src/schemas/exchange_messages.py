from pydantic import BaseModel


class RequestMessage(BaseModel):
    user_id: int
    flight_number: str
    flight_date: str


class ResponseMessage(BaseModel):
    user_id: int
    message: str
