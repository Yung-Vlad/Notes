from datetime import datetime

from fastapi import HTTPException, status
from fastapi_utils.tasks import repeat_every

import base64
from schemas.notes import NoteInternalSchema, NoteUpdateInternalSchema
from typing import Optional

from .general import get_cursor
from .accesses import check_is_owner_of_note


def add_note(note: NoteInternalSchema, from_user: int) -> None:
    """
    Add new note to db
    :param note: all info about this note (header, content, tags)
    :param from_user: user's id who wants to get his notes
    """

    with get_cursor() as cursor:

        key_str = base64.b64encode(note.aes_key).decode()

        cursor.execute("""
            INSERT INTO notes (header, content, tags, aes_key, created_time, active_time, from_user_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (note.header, note.text, note.tags, key_str, note.created_time, note.active_time, from_user))

        # Increment counter for creating notes
        cursor.execute("""
            UPDATE statistics SET count_creating_note = count_creating_note + 1 
            WHERE user_id = ? 
        """, (from_user,))


def get_all_notes(user_id: int, offset: int, limit: int, tags: Optional[str]) -> dict:
    """
    Getting all notes for users by his id
    :param user_id: user's id who want to get his notes
    :param offset: offset from the start of the available notes
    :param limit: count notes for 1 query
    :param tags: filter notes by tags
    """

    with get_cursor() as cursor:

        # Query and parameters
        query = f"""
            SELECT * FROM (
                SELECT * FROM notes WHERE from_user_id = ? 
                UNION
                SELECT id, header, content, tags, accesses.key, from_user_id,
                    created_time, active_time, last_edit_time, last_edit_user 
                FROM notes 
                INNER JOIN accesses ON notes.id = accesses.note_id WHERE accesses.user_id = ?
            )
            {"WHERE tags LIKE %?%" if tags is not None else ""} ORDER BY id LIMIT ? OFFSET ?
        """
        params = [user_id, user_id, tags, limit, offset]

        # If tags is None then remove it from parameters
        if not tags:
            params.remove(tags)

        cursor.execute(query, params)

        data = cursor.fetchall()
        if not data:  # If nothing found
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No notes found!"
            )

        # Increase counter for reading notes
        cursor.execute("""
            UPDATE statistics SET count_reading_note = count_reading_note + ? 
            WHERE user_id = ? 
        """, (len(data), user_id))

        # Return dictionary in understandable format
        return {
            item[0]: {
                "header": item[1], "content": item[2], "tags": item[3],
                "aes_key": item[4], "from_user_id": item[5], "created_time": item[6],
                "active_time": item[7], "last_edit_time": item[8], "last_edit_user": item[9]
            }
            for item in data
        }


def get_note_by_id(note_id: int, user_id: int, by_link=False) -> dict:
    """
    Get note by id for user if he has access for this note
    """

    with get_cursor() as cursor:

        if not by_link:
            cursor.execute("""
                SELECT id, header, content, tags, aes_key, from_user_id, created_time, active_time, last_edit_time, last_edit_user FROM notes
                WHERE id = ? AND from_user_id = ?
                UNION
                SELECT id, header, content, tags, accesses.key, from_user_id, created_time, active_time, last_edit_time, last_edit_user FROM notes
                INNER JOIN accesses ON notes.id = accesses.note_id
                WHERE accesses.note_id = ? AND accesses.user_id = ?
            """, (note_id, user_id, note_id, user_id))

        else:
            cursor.execute("""
                SELECT id, header, content, tags, shared_notes.key, from_user_id, created_time, active_time, last_edit_time, last_edit_user FROM notes
                INNER JOIN shared_notes ON shared_notes.note_id = notes.id
                WHERE note_id = ?
            """, (note_id,))

        data = cursor.fetchone()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found or access denied!"
            )

        # Increment counter for reading notes
        cursor.execute("""
            UPDATE statistics SET count_reading_note = count_reading_note + 1 
            WHERE user_id = ? 
        """, (user_id,))

        return {
            "id": data[0], "header": data[1], "content": data[2], "tags": data[3],
            "aes_key": data[4], "from_user_id": data[5], "created_time": data[6],
            "active_time": data[7], "last_edit_time": data[8], "last_edit_user": data[9]
        }


def get_aes_key(note_id: int, user_id: int) -> str:
    """
    Get aes_key from db to access note by user_id and note_id
    """

    with get_cursor() as cursor:

        if check_is_owner_of_note(user_id, note_id):
            cursor.execute("""
                SELECT aes_key FROM notes WHERE id = ?
            """, (note_id,))
        else:
            cursor.execute("""
                SELECT key FROM accesses WHERE note_id = ? AND user_id = ?
            """, (note_id, user_id))

        data = cursor.fetchone()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AES key not found!"
            )

        return data[0]


def get_shared_key(note_id: int, link: str) -> dict:
    """
    Get aes_key from shared_notes to decrypt note
    """

    with get_cursor() as cursor:

        cursor.execute("""
            SELECT key FROM shared_notes WHERE note_id = ? AND link = ?
        """, (note_id, link))

        data = cursor.fetchone()
        if not data:
            return { "message": "Access denied!" }

        return { "key": data[0] }


def delete_note_by_id(note_id: int, user_id: int) -> dict:
    """
    Delete note by id if user is owner this note
    """

    with get_cursor() as cursor:

        cursor.execute("""
            DELETE FROM notes WHERE id = ? AND from_user_id = ?
        """, (note_id, user_id))

        # If not exist note with :note_id or this user isn't owner this note
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found or access denied!"
            )

        # Delete all accesses for this note
        cursor.execute("""
            DELETE FROM accesses WHERE note_id = ?
        """, (note_id,))

        # Increment counter for deleting notes
        cursor.execute("""
            UPDATE statistics SET count_deleting_note = count_deleting_note + 1 
            WHERE user_id = ? 
        """, (user_id,))

    return { "message": "Note has been successfully deleted" }


def check_access(note_id: int, user_id: int) -> bool:
    """
    Check user access to note
    """

    with get_cursor() as cursor:

        cursor.execute("""
            SELECT * FROM notes WHERE id = ? AND (from_user_id = ? OR 
            EXISTS (SELECT 1 FROM accesses WHERE note_id = ? AND user_id = ? AND permission = 2))
        """, (note_id, user_id, note_id, user_id))

        return bool(cursor.fetchone())


@repeat_every(seconds=60)
async def check_active_time() -> None:
    """
    If active time is over then delete note
    """

    with get_cursor() as cursor:
        curr_time = datetime.now()

        cursor.execute("""
            SELECT id FROM notes WHERE active_time IS NOT NULL AND active_time <= ?
        """, (curr_time,))

        data = cursor.fetchall()
        if not data:
            return

        for (note_id,) in data:
            cursor.execute("""
                DELETE FROM notes WHERE id = ?
            """, (note_id,))

            cursor.execute("""
                DELETE FROM shared_notes WHERE note_id = ?
            """, (note_id,))

            cursor.execute("""
                DELETE FROM accesses WHERE note_id = ?
            """, (note_id,))


def update_note(note: NoteUpdateInternalSchema) -> dict:
    """
    Update note in db after editing
    """

    with get_cursor() as cursor:

        cursor.execute("""
            UPDATE notes SET header = ?, content = ?, tags = ?, active_time = ?, last_edit_time = ?, last_edit_user = ? WHERE id = ?
        """, (note.header, note.text, note.tags, note.active_time, note.last_edit_time, note.last_edit_user, note.id))

    return { "message": "Note has successfully updated" }


def create_shared_note(owner_id: int, note_id: int, key: str, link: str) -> None:

    with get_cursor() as cursor:

        cursor.execute("""
            INSERT INTO shared_notes VALUES (?, ?, ?, ?)
        """, (note_id, owner_id, key, link))

def delete_shared_note(note_id: int) -> None:

    with get_cursor() as cursor:

        cursor.execute("""
            DELETE FROM shared_notes WHERE note_id = ?
        """, (note_id,))
