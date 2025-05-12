from .users import UserCreateSchema


class AdminSchema(UserCreateSchema):
    key: str
