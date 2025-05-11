from pydantic import BaseModel, Field
from enum import Enum


class AccessSchema(BaseModel):
    user_id: int = Field(ge=1)
    note_id: int = Field(ge=1)


class PermissionSchema(str, Enum):
    read: str = "read"
    read_and_write: str = "read and write"


class AccessInternalSchema(AccessSchema):
    permission: int = Field(ge=1, le=2)
    key: str | bytes | None
