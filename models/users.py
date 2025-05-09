from pydantic import BaseModel


class UserLoginModel(BaseModel):
    username: str
    password: str


class UserCreateModel(UserLoginModel):
    repeat_password: str
    email: str


class ResetPasswordModel(BaseModel):
    old_password: str
    new_password: str
    repeat_password: str


class ConfirmRestoringPasswordModel(BaseModel):
    username: str
    email: str


class RestorePasswordModel(BaseModel):
    new_password: str
    repeat_password: str
