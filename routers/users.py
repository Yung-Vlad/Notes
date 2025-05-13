from fastapi import HTTPException, Depends, status, Response, Request, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

import secrets, os, hashlib
from datetime import timedelta, datetime

from database.users import (create_user, get_user, get_statistics, reset_password,
                            get_email, restore_password, check_restore_password_exists, set_refresh_token)
from secure.tokens import JWT, CSRF
from secure.validating import Validator
from schemas.users import UserCreateSchema, ResetPasswordSchema, RestorePasswordSchema, ConfirmRestoringPasswordSchema
from secure.validating import Checker
from secure.hashing import Hasher


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/signup",
             summary="Registration new user")
async def signup(request: Request, user: UserCreateSchema) -> dict:
    if check_logged(request):
        return { "message": "First you need to logout" }

    Checker.check_user_data(user)

    # Hash password and register new user
    user.password = Hasher.get_password_hash(user.password)
    create_user(user)

    return { "message": "User registered successfully" }


@router.post("/signin",
             summary="Authentication user")
async def login(request: Request, response: Response,
                data: OAuth2PasswordRequestForm = Depends()) -> dict:
    if check_logged(request):
        return { "message": "You already logged" }

    user = get_user(data.username)
    username = user["username"]

    # Check username and password
    if not user or not Hasher.verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password!",
            headers={ "WWW-Authenticate": "Bearer" }
        )

    # Create jwt tokens
    access_token = JWT.create_access_token({ "sub": username })
    refresh_token = JWT.create_refresh_token(username)
    hashed_refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    set_refresh_token(username, hashed_refresh_token)

    # Create csrf token
    csrf_token = secrets.token_hex(16)

    # Set jwt to HttpOnlyCookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
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
async def logout(request: Request, response: Response) -> dict:
    if check_logged(request):  # If user is logged in
        response.delete_cookie("access_token")
        response.delete_cookie("csrf_token")
        return { "message": "Logged out" }
    else:
        return { "message": "You aren't logged yet!" }


@router.patch("/reset-password", summary="Reset password",
             description="Change old password to new")
async def change_password(password: ResetPasswordSchema,
                          curr_user: dict = Depends(JWT.get_current_user),
                          _ = Depends(CSRF.verify_csrf_token)) -> dict:
    user_id = curr_user["id"]
    user_password = curr_user["password"]

    # Check old password
    if not Hasher.verify_password(password.old_password, user_password):
        return { "message": "Invalid old password!" }

    # Check new passwords on identity
    if password.new_password != password.repeat_password:
        return { "message": "New passwords aren't the same!" }

    # Check old and new passwords on identity
    if password.old_password == password.new_password:
        return { "message": "You can't change your password to your old password!" }

    password_error = Validator.check_password_complexity(password.new_password)
    if password_error is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=password_error)

    # Hash password and change it
    password.new_password = Hasher.get_password_hash(password.new_password)
    reset_password(user_id, password.new_password)

    return { "message": "Password was changed successfully" }


@router.post("/confirm-recover-password", summary="Restore password",
             description="Confirming to restore password if user forget it")
async def confirm_recover_password(request: Request,
                                   user_data: ConfirmRestoringPasswordSchema) -> dict:
    if check_logged(request):
        return { "message": "You are already logged in" }

    # Check username and email
    user = get_user(user_data.username)
    if user is None:
        return { "message": "Invalid username!" }

    user_id = user["id"]
    user_email = get_email(user_id)
    if user_email != user_data.email:
        return { "message": "Invalid email!" }

    # If already send recovery request
    check_existing = check_restore_password_exists(user_id)
    if check_existing is not None:
        return { "message": "Check your email pls!" }

    # Add key_code to db
    key_code = os.urandom(12)  # Random key_code for access
    expired_time = datetime.now() + timedelta(hours=1)  # Expired access time

    return restore_password(user_id, key_code, expired_time, user_email)


@router.get("/verify-recover-password/{user_id}/{key_code}", summary="Restore password",
             description="Restore password if user forget it")
async def verify_recover_password(user_id: int, key_code: str) -> dict:
    # Check link
    check_existing = check_restore_password_exists(user_id)
    if check_existing is None or check_existing != key_code:
        return { "message": "Access denied or link timed out" }

    return { "message": "Nice" }


@router.patch("/recover-password/{username}", summary="Restore password",
             description="Restore password if user forget it")
async def recover_password(username: str, password: RestorePasswordSchema) -> dict:
    # Check new password
    if password.new_password != password.repeat_password:
        return { "message": "New passwords aren't the same!" }

    user = get_user(username)
    # Check old and new passwords on identity
    if Hasher.verify_password(password.new_password, user["password"]):
        return { "message": "You can't change your password to your old password!" }

    password_error = Validator.check_password_complexity(password.new_password)
    if password_error is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=password_error)

    # Hash password and change it
    password.new_password = Hasher.get_password_hash(password.new_password)
    reset_password(user["id"], password.new_password)

    return { "message": "Password was changed successfully" }


@router.get("/statistics",
            summary="Get activity statistics",
            description="Getting statistics about user activity by id")
async def statistics(curr_user: dict = Depends(JWT.get_current_user),
               _ = Depends(CSRF.verify_csrf_token)) -> dict:
    user_id = curr_user["id"]

    return get_statistics(user_id)


# Check if user logged
def check_logged(request: Request) -> bool:
    return bool(request.cookies.get("access_token"))
