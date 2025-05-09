from fastapi import HTTPException, Depends, status, Response, Request, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

import secrets
from datetime import timedelta

from database.users import create_user, get_user, get_statistics, reset_password
from secure.tokens import JWT, CSRF
from secure.validating import Validator
from models.users import UserCreateModel, ResetPasswordModel, RestorePasswordModel, ConfirmRestoringPasswordModel
from secure.validating import Checker
from secure.hashing import Hasher


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/signup",
             summary="Registration new user")
def signup(request: Request, user: UserCreateModel) -> dict:
    if check_logged(request):
        return { "message": "First you need to logout" }

    Checker.check_user_data(user)

    # Hash password and register new user
    user.password = Hasher.get_password_hash(user.password)
    create_user(user)

    return { "message": "User registered successfully" }


@router.post("/signin",
             summary="Authentication user")
def login(request: Request, response: Response, data: OAuth2PasswordRequestForm = Depends()) -> dict:
    if check_logged(request):
        return { "message": "You already logged" }

    user = get_user(data.username)

    # Check username and password
    if not user or not Hasher.verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password!",
            headers={ "WWW-Authenticate": "Bearer" }
        )

    # Create jwt access token
    access_token_expires = timedelta(minutes=JWT.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = JWT.create_access_token({ "sub": user["username"] },
                                       access_token_expires)

    # Create csrf token
    csrf_token = secrets.token_hex(16)

    # Set jwt to HttpOnlyCookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=60 * JWT.ACCESS_TOKEN_EXPIRE_MINUTES,
        samesite="lax"
    )

    # Set csrf to cookie
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        samesite="lax"
    )

    return { "message": "Login successfully 😉" }


@router.post("/logout",
             summary="Logout from service")
def logout(request: Request, response: Response) -> dict:
    if check_logged(request):  # If user is logged in
        response.delete_cookie("access_token")
        response.delete_cookie("csrf_token")
        return { "message": "Logged out" }
    else:
        return { "message": "You aren't logged yet!" }


@router.patch("/reset-password", summary="Reset password",
             description="Change old password to new")
def change_password(password: ResetPasswordModel,
                    curr_user: dict = Depends(JWT.get_current_user),
                    _ = Depends(CSRF.verify_csrf_token)) -> dict:
    user_id = curr_user["id"]
    user_password = curr_user["password"]

    # Check old password
    if not Hasher.verify_password(password.old_password, user_password):
        return { "message": "Invalid old password!" }

    # Check new passwords identity
    if password.new_password != password.repeat_password:
        return { "message": "Passwords aren't identity!" }

    # Check old and new passwords identity
    if password.old_password == password.new_password:
        return { "message": "You can't change your password to your old password!" }

    password_error = Validator.check_password_complexity(password.new_password)
    if password_error is not None:
        raise HTTPException(status_code=400, detail=password_error)

    # Hash password and change it
    password.new_password = Hasher.get_password_hash(password.new_password)
    reset_password(user_id, password.new_password)

    return { "message": "Password was changed successfully" }


@router.post("/recover-password", summary="Restore password",
             description="Restore password if user forget it")
def restore_password(user_data: ConfirmRestoringPasswordModel) -> dict:
    ...


@router.patch("/recover-password/{user_id}/{key_code}", summary="Restore password",
             description="Restore password if user forget it")
def restore_password(user_id: int, key_code: str) -> dict:
    ...


@router.get("/statistics",
            summary="Get activity statistics",
            description="Getting statistics about user activity by id")
def statistics(curr_user: dict = Depends(JWT.get_current_user),
               _ = Depends(CSRF.verify_csrf_token)) -> dict:
    user_id = curr_user["id"]

    return get_statistics(user_id)


# Check if user logged
def check_logged(request: Request) -> bool:
    return bool(request.cookies.get("access_token"))
