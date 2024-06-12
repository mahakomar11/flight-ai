from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    id: int
    phone: str
    answers: Optional[dict] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
