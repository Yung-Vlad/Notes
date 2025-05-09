import re
from zxcvbn import zxcvbn
from fastapi import HTTPException

from database.users import get_user
from database.general import check_existing_email
from models.users import UserCreateModel
from models.admins import AdminModel


class Checker:
    @staticmethod
    def check_user_data(user: UserCreateModel | AdminModel) -> None:
        # Check username
        existing_user = get_user(user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already busy!")

        # Check password
        if user.password != user.repeat_password:
            raise HTTPException(status_code=400, detail="Passwords aren't identity!")

        password_error = Validator.check_password_complexity(user.password)
        if password_error is not None:
            raise HTTPException(status_code=400, detail=password_error)

        # Check existing email
        existing_email = check_existing_email(user.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already busy!")

        # Check valid email
        if not Validator.check_valid_email(user.email):
            raise HTTPException(status_code=400, detail="Email isn't valid!")


class Validator:
    @staticmethod
    def check_password_complexity(password: str) -> str | None:
        if len(password) < 8:  # Length
            return "Password is too short!"
        elif not bool(re.search(r'\d', password)):  # Exists numbers
            return "Password must contain number(s)!"
        elif not bool(re.search(r"[A-Za-z]", password)):  # Exists letters
            return "Password must contain letter(s)!"
        elif zxcvbn(password)["score"] < 2:  # Password strength
            return "Password is too easy!"

        return None

    @staticmethod
    def check_valid_email(email: str) -> bool:
        pattern: str = r"^[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        return bool(re.match(pattern, email))
