from fastapi import HTTPException, Request, status, Depends
from fastapi.security import OAuth2PasswordBearer

import jwt, os
from datetime import datetime, timedelta, UTC

from database.users import get_user


class JWT:
    __KEY: str = os.getenv("KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20
    __ALGORITHM: str = "HS256"
    __oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/signin")

    # Create JWT
    @staticmethod
    def create_access_token(data: dict, expires_time: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.now(UTC) + expires_time
        to_encode.update({"exp": expire})

        return jwt.encode(to_encode, JWT.__KEY, JWT.__ALGORITHM)

    # Get user by JWT
    @staticmethod
    def get_current_user(request: Request) -> dict:
        auth_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authentication data",
            headers={ "WWW-Authenticate": "Bearer" }
        )

        try:
            token = request.cookies.get("access_token")
            if not token:
                raise auth_exception

            payload = jwt.decode(token, JWT.__KEY, JWT.__ALGORITHM)

            username = payload.get("sub")
            if not username:
                raise auth_exception

        except jwt.PyJWTError:
            raise auth_exception

        user = get_user(username)
        if not user:
            raise auth_exception

        return user

    # Check admin by JWT
    @staticmethod
    def get_admin(curr_user: dict = Depends(get_current_user)) -> dict:
        if not curr_user["is_admin"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Access denied!")

        return curr_user


class CSRF:
    @staticmethod
    def verify_csrf_token(request: Request) -> None:
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")

        # Emulate csrf security
        if not csrf_header and csrf_cookie:
            csrf_header = csrf_cookie

        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="CSRF token is missing or invalid!")
