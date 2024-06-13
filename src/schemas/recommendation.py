import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Recommendation(BaseModel):
    id: str | uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: int
    message: str
    scheduled_at: datetime
    delivered: bool = False

    model_config = ConfigDict(from_attributes=True)
