from pydantic import BaseModel


class NoteModel(BaseModel):
    header: str
    text: str
    tags: str | None


class NoteInternalModel(NoteModel):
    created_time: str
    aes_key: str | bytes


class NoteUpdateModel(NoteModel):
    id: int


class NoteUpdateInternalModel(NoteUpdateModel):
    last_edit_time: str
    last_edit_user: int
