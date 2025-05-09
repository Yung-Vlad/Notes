from pydantic import BaseModel, Field, EmailStr


class UserLoginSchema(BaseModel):
    username: str = Field(max_length=15)
    password: str = Field(max_length=25)


class UserCreateSchema(UserLoginSchema):
    repeat_password: str = Field(max_length=25)
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    old_password: str = Field(max_length=25)
    new_password: str = Field(max_length=25)
    repeat_password: str = Field(max_length=25)


class ConfirmRestoringPasswordSchema(BaseModel):
    username: str = Field(max_length=15)
    email: EmailStr


class RestorePasswordSchema(BaseModel):
    new_password: str = Field(max_length=25)
    repeat_password: str = Field(max_length=25)
