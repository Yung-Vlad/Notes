from fastapi import HTTPException, Request, Response, status, Depends
from fastapi.security import OAuth2PasswordBearer

import jwt, os, secrets, hashlib, hmac
from pathlib import Path
from datetime import datetime, timedelta, UTC

from database.users import get_user, set_refresh_token, get_refresh_token


class JWT:
    __KEY: str = os.getenv("KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    __ALGORITHM: str = "HS256"
    __PRIVATE_KEYS_PATH = "private_keys"
    __oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/signin")

    # Create JWT
    @staticmethod
    def create_access_token(data: dict, expires_time: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(minutes=expires_time)
        to_encode.update({"exp": expire, "sub": data.get("sub")})

        return jwt.encode(to_encode, JWT.__KEY, JWT.__ALGORITHM)

    @staticmethod
    def create_refresh_token(username: str, expires_days: int = REFRESH_TOKEN_EXPIRE_DAYS) -> str:
        expire = datetime.now(UTC) + timedelta(days=expires_days)
        to_encode = {
            "exp": expire,
            "sub": username
        }

        return jwt.encode(to_encode, JWT.__load_user_key(username), JWT.__ALGORITHM)

    @staticmethod
    def generate_user_key(username: str) -> str:
        Path(JWT.__PRIVATE_KEYS_PATH).mkdir(parents=True, exist_ok=True)
        key = secrets.token_hex(32)  # secret key

        key_path = Path(JWT.__PRIVATE_KEYS_PATH) / f"{username}.key"
        key_path.write_text(key)

        return key

    @staticmethod
    def __load_user_key(username: str) -> str:
        key_path = Path(JWT.__PRIVATE_KEYS_PATH) / f"{username}.key"
        if not key_path.exists():
            raise FileNotFoundError(f"Key for user {username} not found!")

        return key_path.read_text()

    @staticmethod
    def __compare_refresh_tokens(username: str, provided_token: str) -> bool:
        stored_token = get_refresh_token(username)  # hashed token from db
        hashed_token = hashlib.sha256(provided_token.encode()).hexdigest()
        return hmac.compare_digest(stored_token, hashed_token)

    # Get user by JWT
    @staticmethod
    def get_current_user(request: Request, response: Response) -> dict:
        auth_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authentication data",
            headers={ "WWW-Authenticate": "Bearer" }
        )

        try:  # Try access token
            access_token = request.cookies.get("access_token")
            if not access_token:
                raise auth_exception

            payload = jwt.decode(access_token, JWT.__KEY, JWT.__ALGORITHM)
            username = payload.get("sub")

        except jwt.PyJWTError:  # Try refresh token
            try:
                refresh_token = request.cookies.get("refresh_token")
                if not refresh_token:
                    raise auth_exception

                unverified = jwt.decode(refresh_token, options={"verify_signature": False})
                username = unverified.get("sub")
                if not username:
                    raise auth_exception

                if not JWT.__compare_refresh_tokens(username, refresh_token):
                    raise auth_exception

                # Create jwt tokens
                access_token = JWT.create_access_token({"sub": username})
                refresh_token = JWT.create_refresh_token(username)
                hashed_refresh_token = hashlib.sha256(refresh_token.encode()).hexdigest()
                set_refresh_token(username, hashed_refresh_token)

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
