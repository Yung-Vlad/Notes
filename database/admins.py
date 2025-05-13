from fastapi import HTTPException, status

import os

from .general import get_cursor
from cipher.generate import KEYS_PATH


def delete_notes_by_user_id(user_id: int) -> dict:
    """
    Delete all notes which belong specific user
    """

    with get_cursor() as cursor:

        # Delete all accesses for this notes
        cursor.executescript("""
            DELETE FROM accesses WHERE note_id IN (SELECT id FROM notes WHERE from_user_id = ?);
            DELETE FROM notes WHERE from_user_id = ?;
            DELETE FROM shared_notes WHERE user_id = ?;
        """, (user_id, user_id, user_id))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notes not found"
            )

    return { "message": "Notes are successfully deleted" }


def delete_statistics_by_user_id(user_id: int) -> None:
    """
    Delete statistics for specific user
    """

    with get_cursor() as cursor:

        cursor.execute("""
            DELETE FROM statistics WHERE user_id = ?
        """, (user_id,))


def delete_user_by_id(user_id: int, himself=False) -> dict:
    with get_cursor() as cursor:

        cursor.execute("""
            SELECT username FROM users WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Delete private key
        delete_user_pkey(row[0])

        cursor.execute(f"""
            DELETE FROM users WHERE id = ? {not himself if "AND is_admin = 0" else ""}
        """, (user_id,))

        # Delete his notes and statistics
        delete_notes_by_user_id(user_id)
        delete_statistics_by_user_id(user_id)

    return { "message": "User is successfully deleted" }


def delete_note_by_id(note_id: int) -> dict:
    with get_cursor() as cursor:

        cursor.executescript("""
            DELETE FROM notes WHERE id = ?;
            DELETE FROM shared_notes WHERE note_id = ?;
            DELETE FROM accesses WHERE note_id = ?;
        """, (note_id, note_id, note_id))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )

    return {"message": "Note is successfully deleted"}


def delete_all_users() -> dict:
    with get_cursor() as cursor:

        cursor.execute("""
            SELECT username FROM users WHERE is_admin = 0
        """)

        row = cursor.fetchall()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No users found"
            )

        # Delete private keys
        delete_user_pkey([name[0] for name in row])

        cursor.executescript("""
            DELETE FROM users WHERE is_admin = 0;
            DELETE FROM notes WHERE from_user_id NOT IN (SELECT id FROM users);
            DELETE FROM statistics WHERE user_id NOT IN (SELECT id FROM users);
            DELETE FROM accesses WHERE user_id NOT IN (SELECT id FROM users);
        """)

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Private key not found!")
