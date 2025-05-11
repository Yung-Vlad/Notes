from fastapi import HTTPException, status

import sqlite3, base64
from datetime import datetime
from schemas.admins import AdminSchema
from schemas.users import UserCreateSchema
from .general import get_cursor
from cipher.generate import generate_asymmetric_keys
from secure.notification import notify


def get_user(username: str) -> dict | None:
    """
    Getting user from db by username
    """

    with get_cursor() as cursor:

        cursor.execute("""
            SELECT * FROM users WHERE username = ?
        """, (username, ))

        user = cursor.fetchone()
        if user:
            return { "id": user[0], "username": user[1], "password": user[2], "email": user[3], "is_admin": user[4] }

    return None


def create_user(user: UserCreateSchema | AdminSchema, is_admin=False) -> None:
    """
    Registration new user or admin and adding him to db
    """

    # Get pub_key
    public_key = generate_asymmetric_keys(user.username)

    with get_cursor() as cursor:

        # Table users
        cursor.execute("""
            INSERT INTO users (username, password, email, public_key, is_admin) VALUES (?, ?, ?, ?, ?)
        """, (user.username, user.password, user.email, public_key, is_admin))

        # Table statistics
        cursor.execute("""
            INSERT INTO statistics VALUES ((SELECT id FROM users WHERE username = ?), ?, ?, ?)
        """, (user.username, 0, 0, 0))


def reset_password(user_id: int, new_password: str) -> None:
    """
    Reset password for user by user_id
    """

    with get_cursor() as cursor:

        cursor.execute("""
            UPDATE users SET password = ? WHERE id = ?
        """, (new_password, user_id))


def get_statistics(user_id: int) -> dict:
    """
    Get statistics for specific user
    """

    with get_cursor() as cursor:

        cursor.execute("""
            SELECT users.username, 
                   users.email, 
                   statistics.count_creating_note, 
                   statistics.count_reading_note, 
                   statistics.count_deleting_note
            FROM users
            INNER JOIN statistics ON users.id = statistics.user_id 
            WHERE users.id = ?
        """, (user_id,))

        data = cursor.fetchone()
        if not data or len(data) < 5:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Something went wrong..."
            )

        return {
            "username": data[0], "email": data[1], "statistics": {
                "created": data[2],
                "read": data[3],
                "deleted": data[4]
            }
        }


def restore_password(user_id: int, key_code: bytes, expired_time: datetime, email: str) -> dict:
    check_expired_time()

    with get_cursor() as cursor:

        cursor.execute("""
            INSERT INTO password_restore VALUES (?, ?, ?)
        """, (user_id, key_code, expired_time))

        # Send email
        notify(email,f"Restore your password: "
                     f"http://127.0.0.1/users/verify-recover-password/{user_id}/{base64.b64encode(key_code).decode()}, "
                     f"expires in: {expired_time.strftime('%H:%M %d-%m-%Y')}")

    return { "message": "Confirm recovering on your email" }


def check_restore_password_exists(user_id: int) -> str | None:
    """
    If user already send recovery password request
    """

    with get_cursor() as cursor:

        cursor.execute("""
            SELECT key FROM password_restore WHERE user_id = ? AND expired_at > ?
        """, (user_id, datetime.now()))

        key = cursor.fetchone()
        if key is None:
            return None

        return base64.b64encode(key[0]).decode()


def check_expired_time() -> None:
    """
    If time is expired then delete access from table
    """

    with get_cursor() as cursor:

        cursor.execute("""
            DELETE FROM password_restore WHERE expired_at < ?
        """, (datetime.now(), ))


def get_email(user_id: int) -> str:
    with get_cursor() as cursor:

        cursor.execute("""
            SELECT email FROM users WHERE id = ?
        """, (user_id,))

        return cursor.fetchone()[0]


def get_public_key(user_id: int) -> bytes:
    with get_cursor() as cursor:

        cursor.execute("""
            SELECT public_key FROM users WHERE id = ?
        """, (user_id,))

        return str(cursor.fetchone()[0]).encode()
