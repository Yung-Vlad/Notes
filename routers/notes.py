from fastapi import APIRouter, Depends, Query, HTTPException

import base64
from typing import Optional
from datetime import datetime

from secure.tokens import JWT, CSRF
from models.notes import NoteModel, NoteUpdateModel, NoteInternalModel, NoteUpdateInternalModel
from cipher.encrypting import symmetric_encrypt_note, encrypt_aes_key
from cipher.decrypting import decrypt_note, decrypt_aes_key, get_private_key
from cipher.generate import generate_aes_key
from database.users import get_public_key
from database.notes import (add_note, delete_note_by_id,
                            get_all_notes, get_note_by_id,
                            check_access, update_note, get_aes_key)


router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post("/create",
          summary="Adding new note",
          description="Adding new note which contain: header, text (main content) and tags (if needed)")
def create_note(note: NoteModel,
                curr_user: dict = Depends(JWT.get_current_user),
                _ = Depends(CSRF.verify_csrf_token)) -> dict:
    if not note.header or not note.text:
        raise HTTPException(status_code=400, detail="Incorrect input of note!")

    user_id = curr_user["id"]
    public_key = get_public_key(user_id)
    aes_key = generate_aes_key()
    note = NoteInternalModel(**note.dict(), aes_key=encrypt_aes_key(public_key, aes_key), created_time=datetime.now().strftime("%H:%M:%S %d-%m-%Y"))

    add_note(symmetric_encrypt_note(aes_key, note), user_id)

    return { "message": "Note added successfully" }


@router.get("/",
         summary="Viewing all notes",
         description="Viewing all notes which you posted")
def get_notes(curr_user: dict = Depends(JWT.get_current_user),
              _ = Depends(CSRF.verify_csrf_token),
              page: int = Query(1, ge=1, description="Page number"),
              limit: int = Query(10, ge=1, le=100, description="Notes per page"),
              tags: Optional[str] = Query(None, description="Filter by tag(s)")) -> dict:

    user_id = curr_user["id"]
    username = curr_user["username"]
    offset = (page - 1) * limit

    # Get all encrypted notes
    notes = get_all_notes(user_id, offset, limit, tags)
    if "message" in notes.keys():  # If no notes
        return notes

    decrypted_notes = {}

    # Decrypted receiver notes
    for key_note in notes.keys():
        aes_key = base64.b64decode(notes[key_note]["aes_key"])
        decrypted_notes.update({ key_note: decrypt_note(notes[key_note], username, aes_key) })
        del decrypted_notes[key_note]["aes_key"]

    return { "notes": decrypted_notes }


@router.get("/{note_id}",
         summary="Viewing note by id")
def get_note(note_id: int,
             curr_user: dict = Depends(JWT.get_current_user),
             _ = Depends(CSRF.verify_csrf_token)) -> dict:
    user_id = curr_user["id"]
    username = curr_user["username"]

    note = get_note_by_id(note_id, user_id)
    aes_key = note["aes_key"]
    if aes_key == "None":  # If no aes_key
        raise HTTPException(status_code=400, detail="Note not found!")

    decrypted_note = decrypt_note(note, username, base64.b64decode(aes_key))
    del note["aes_key"]

    return { "note": decrypted_note }


@router.delete("/{note_id}",
            summary="Deleting note by id")
def delete_note(note_id: int,
                curr_user: dict = Depends(JWT.get_current_user),
                _ = Depends(CSRF.verify_csrf_token)) -> dict:
    user_id = curr_user["id"]

    return delete_note_by_id(note_id, user_id)


@router.put("/edit-note/{note_id}",
            summary="Editing note")
def editing_note(note: NoteUpdateModel,
                 curr_user: dict = Depends(JWT.get_current_user),
                 _ = Depends(CSRF.verify_csrf_token)) -> dict:

    if not check_access(note.id, curr_user["id"]):
        return { "message": "Note not found or access denied" }

    if not note.header or not note.text:
        raise HTTPException(status_code=400, detail="Incorrect input of note!")

    user_id = curr_user["id"]
    username = curr_user["username"]

    private_key = get_private_key(username)  # Private key of user who want to edit this note
    note = NoteUpdateInternalModel(**note.dict(), last_edit_time=datetime.now().strftime("%H:%M:%S %d-%m-%Y"), last_edit_user=user_id)
    aes_key = base64.b64decode(get_aes_key(note.id, user_id))  # Get AES key for accessing to this note

    decrypted_aes_key = decrypt_aes_key(private_key, aes_key)  # Decrypted aes_key

    return update_note(symmetric_encrypt_note(decrypted_aes_key, note))
