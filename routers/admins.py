from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

import os, shutil
from dotenv import load_dotenv
from datetime import date

from .users import check_logged
from secure.tokens import JWT, CSRF
from secure.hashing import Hasher
from secure.validating import Checker
from models.admins import AdminModel
from database.general import DB_PATH
from database.admin import delete_user_by_id, delete_note_by_id, delete_all_users
from database.users import create_user


load_dotenv()
BACKUP_FOLDER = os.getenv("BACKUP_FOLDER")
ADMIN_KEY = os.getenv("ADMIN_KEY")

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/create-admin", summary="Create superuser (admin)")
def create_admin(request: Request, admin: AdminModel) -> dict:
    if check_logged(request):
        return { "message": "First you need to logout" }

    if admin.key != ADMIN_KEY:
        raise HTTPException(status_code=400, detail="Invalid admin key!")

    Checker.check_user_data(admin)

    admin.password = Hasher.get_password_hash(admin.password)
    create_user(admin, True)

    return { "message": "Admin successfully created" }


@router.post("/backup", summary="Create db backup")
def backup(_ = Depends(JWT.get_admin),
           __ = Depends(CSRF.verify_csrf_token)) -> dict:
    if not os.path.exists(BACKUP_FOLDER):  # If not exists folder for backups
        os.mkdir(BACKUP_FOLDER)

    backup_path = os.path.join(BACKUP_FOLDER, "backup.sqlite3")
    shutil.copy(DB_PATH, backup_path)

    return { "message": f"Backup successfully created: {backup_path}" }


@router.get("/download-backup", summary="Download backup if exists to local")
def download_backup(_: dict = Depends(JWT.get_admin),
                    __: None = Depends(CSRF.verify_csrf_token)) -> FileResponse:
    backup_path = os.path.join(BACKUP_FOLDER, "backup.sqlite3")

    if not os.path.exists(backup_path):  # If not exist any backups
        raise HTTPException(status_code=404, detail="Backup files not found!")

    return FileResponse(backup_path, filename=f"backup ({date.today()}).sqlite3")


@router.delete("/delete-user/{user_id}", summary="Delete user by id")
def delete_user(user_id: int,
                _ = Depends(JWT.get_admin),
                __ = Depends(CSRF.verify_csrf_token)) -> dict:

    return delete_user_by_id(user_id)


@router.delete("/delete-users", summary="Delete all users")
def delete_users(_ = Depends(JWT.get_admin),
                __ = Depends(CSRF.verify_csrf_token)) -> dict:

    return delete_all_users()


@router.delete("/delete-note/{note_id}", summary="Delete note by id")
def delete_note(note_id: int,
                _=Depends(JWT.get_admin),
                __=Depends(CSRF.verify_csrf_token)) -> dict:

    return delete_note_by_id(note_id)
