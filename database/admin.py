import sqlite3, os

from .general import DB_PATH
from cipher.generate import KEYS_PATH


def delete_notes_by_user_id(user_id: int) -> dict:
    """
    Delete all notes which belong specific user
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Delete all accesses for this notes
        cursor.execute("""
            DELETE FROM accesses WHERE note_id IN (SELECT id FROM notes WHERE from_user_id = ?)
        """, (user_id,))

        cursor.execute("""
            DELETE FROM notes WHERE from_user_id = ?
        """, (user_id,))

        if cursor.rowcount == 0:
            return {"message": "Notes not found"}

        conn.commit()

        return {"message": "Notes are successfully deleted"}


def delete_statistics_by_user_id(user_id: int) -> None:
    """
    Delete statistics for specific user
    """

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM statistics WHERE user_id = ?
        """, (user_id,))
        conn.commit()


def delete_user_by_id(user_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username FROM users WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            return { "message": "User not found" }

        # Delete private key
        delete_user_pkey(row[0])

        cursor.execute("""
            DELETE FROM users WHERE id = ? AND is_admin = 0
        """, (user_id,))
        conn.commit()

        # Delete his notes and statistics
        delete_notes_by_user_id(user_id)
        delete_statistics_by_user_id(user_id)

        return {"message": "User is successfully deleted"}


def delete_note_by_id(note_id: int) -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM notes WHERE id = ?
        """, (note_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return {"message": "Note not found"}

        return {"message": "Note is successfully deleted"}


def delete_all_users() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username FROM users WHERE is_admin = 0
        """)

        row = cursor.fetchall()
        if not row:
            return { "message": "No users found" }

        # Delete private keys
        delete_user_pkey([name[0] for name in row])

        cursor.executescript("""
            DELETE FROM users WHERE is_admin = 0;
            DELETE FROM notes WHERE from_user_id NOT IN (SELECT id FROM users);
            DELETE FROM statistics WHERE user_id NOT IN (SELECT id FROM users);
            DELETE FROM accesses WHERE user_id NOT IN (SELECT id FROM users);
        """)
        conn.commit()

        return { "message": "All usual users and their notes, statistics and keys are deleted" }


# Delete private key by username
def delete_user_pkey(username: str | list) -> None:
    try:
        if username is list:
            for name in username:
                os.remove(f"{KEYS_PATH}/{name}_key.pem")
            return

        os.remove(f"{KEYS_PATH}/{username}_key.pem")
    except FileNotFoundError as e:
        print(e)
