from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class NoteSchema(BaseModel):
    header: str = Field(max_length=30)
    text: str  = Field(max_length=200)
    tags: str | None = Field(max_length=50)
    active_time: datetime | str | None = Field(default=datetime.now().strftime("%H:%M %d-%m-%Y"))

    @field_validator("active_time")
    def str_to_datetime(cls, value: object) -> object:
        print("abc")
        if isinstance(value, str):
            return datetime.strptime(value, "%H:%M %d-%m-%Y")

        return value


class NoteInternalSchema(NoteSchema):
    created_time: str
    aes_key: str | bytes


class NoteUpdateSchema(NoteSchema):
    id: int = Field(ge=1)


class NoteUpdateInternalSchema(NoteUpdateSchema):
    last_edit_time: str
    last_edit_user: int = Field(ge=1)
