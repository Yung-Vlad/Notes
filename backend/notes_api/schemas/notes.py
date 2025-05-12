from pydantic import BaseModel, Field


class NoteSchema(BaseModel):
    header: str = Field(max_length=30)
    text: str  = Field(max_length=200)
    tags: str | None = Field(max_length=50)


class NoteInternalSchema(NoteSchema):
    created_time: str
    aes_key: str | bytes


class NoteUpdateSchema(NoteSchema):
    id: int = Field(ge=1)


class NoteUpdateInternalSchema(NoteUpdateSchema):
    last_edit_time: str
    last_edit_user: int = Field(ge=1)
