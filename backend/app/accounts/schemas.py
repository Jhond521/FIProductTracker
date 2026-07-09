import uuid

from pydantic import BaseModel, ConfigDict


class GoogleAuthRequest(BaseModel):
    credential: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    picture_url: str | None = None
