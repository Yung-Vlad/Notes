from .users import UserCreateModel


class AdminModel(UserCreateModel):
    key: str
