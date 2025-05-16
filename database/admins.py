from fastapi import HTTPException, status

import os

from secure.notification import notify
from .general import get_cursor
from cipher.generate import KEYS_PATH
from .users import get_email, get_user


def delete_notes_by_user_id(user_id: int) -> dict:
    """
    Delete all notes which belong specific user
    """

    with get_cursor() as cursor:

        # Delete all accesses for this notes
        cursor.execute("""
            DELETE FROM accesses WHERE note_id IN (SELECT id FROM notes WHERE from_user_id = ?);
        """, (user_id,))

        cursor.execute("""
            DELETE FROM notes WHERE from_user_id = ?;
        """, (user_id,))

        cursor.execute("""
            DELETE FROM shared_notes WHERE user_id = ?;
        """, (user_id,))

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


def delete_user_by_id(user_id: int, admin_id: int, himself=False) -> dict:
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

        notify_user_about_deleting(row[0], admin_id, None)

        cursor.execute(f"""
            DELETE FROM users WHERE id = ? {"AND is_admin = 0" if not himself else ""}
        """, (user_id,))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or access denied!"
            )

        # Delete private key
        delete_user_keys(row[0])

        # Delete his notes and statistics
        delete_notes_by_user_id(user_id)
        delete_statistics_by_user_id(user_id)

    return { "message": "User is successfully deleted" }


def delete_note_by_id(note_id: int, admin_id: int) -> dict:
    with get_cursor() as cursor:

        cursor.execute("""
            SELECT username FROM users
            INNER JOIN notes ON users.id = notes.from_user_id
            WHERE notes.id = ?
        """, (note_id,))

        username = cursor.fetchone()[0]

        # Delete note and all accesses
        cursor.execute("""
            DELETE FROM shared_notes WHERE note_id = ?;
        """, (note_id,))

        cursor.execute("""
            DELETE FROM accesses WHERE note_id = ?;
        """, (note_id,))

        cursor.execute("""
            DELETE FROM notes WHERE id = ?;
        """, (note_id,))

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )

        notify_user_about_deleting(username, admin_id, note_id)

    return {"message": "Note is successfully deleted"}


def delete_all_users(admin_id: int) -> dict:
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

        for (username,) in row:
            notify_user_about_deleting(username, admin_id, None)

        # Delete private keys
        delete_user_keys([name[0] for name in row])

        cursor.executescript("""
            DELETE FROM users WHERE is_admin = 0;
            DELETE FROM notes WHERE from_user_id NOT IN (SELECT id FROM users);
            DELETE FROM statistics WHERE user_id NOT IN (SELECT id FROM users);
            DELETE FROM accesses WHERE user_id NOT IN (SELECT id FROM users);
        """)

    return { "message": "All usual users and their notes, statistics and keys are deleted" }


# Delete private key by username
def delete_user_keys(username: str | list) -> None:
    try:
        if isinstance(username, list):
            for name in username:
                os.remove(f"{KEYS_PATH}/{name}_key.pem")
                os.remove(f"{KEYS_PATH}/{name}.key")
            return

        os.remove(f"{KEYS_PATH}/{username}_key.pem")
        os.remove(f"{KEYS_PATH}/{username}.key")
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Private key not found!")


# Notify user about deleting note or account
def notify_user_about_deleting(username: str, admin_id: int, note_id: int | None) -> None:
    user = get_user(username)

    email = get_email(user["id"])
    text = f"Admin with id: {admin_id} "
    text += "deleted your account and all of your notes" if note_id is None else f"deleted your note with id: {note_id}"

    notify(email, text)
