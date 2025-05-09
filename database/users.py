import sqlite3
from models.admins import AdminModel
from models.users import UserCreateModel
from .general import DB_PATH
from cipher.generate import generate_asymmetric_keys


def get_user(username: str) -> dict[str: str] | None:
    """
    Getting user from db by username
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE username = ?
        """, (username, ))

        user = cursor.fetchone()
        if user:
            return { "id": user[0], "username": user[1], "password": user[2], "email": user[3], "is_admin": user[4] }

        return None


def create_user(user: UserCreateModel | AdminModel, is_admin=False) -> None:
    """
    Registration new user or admin and adding him to db
    """

    # Get pub_key
    public_key = generate_asymmetric_keys(user.username)

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Table users
        cursor.execute("""
            INSERT INTO users (username, password, email, public_key, is_admin) VALUES (?, ?, ?, ?, ?)
        """, (user.username, user.password, user.email, public_key, is_admin))
        conn.commit()

        # Table statistics
        cursor.execute("""
            INSERT INTO statistics VALUES ((SELECT id FROM users WHERE username = ?), ?, ?, ?)
        """, (user.username, 0, 0, 0))
        conn.commit()


def reset_password(user_id: int, new_password: str) -> None:
    """
    Reset password for user by user_id
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users SET password = ? WHERE id = ?
        """, (new_password, user_id))
        conn.commit()


def get_statistics(user_id: int) -> dict:
    """
    Get statistics for specific user
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

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
            return { "message": "Something went wrong..." }

        return {
            "username": data[0], "email": data[1], "statistics": {
                "created": data[2],
                "read": data[3],
                "deleted": data[4]
            }
        }


def get_email(user_id: int) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT email FROM users WHERE id = ?
        """, (user_id,))

        return cursor.fetchone()[0]


def get_public_key(user_id: int) -> bytes:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT public_key FROM users WHERE id = ?
        """, (user_id,))

        return str(cursor.fetchone()[0]).encode()
