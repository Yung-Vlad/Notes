from fastapi import APIRouter, Depends

import base64
from schemas.accesses import AccessSchema, AccessInternalSchema, PermissionSchema
import database.accesses as db
from database.users import get_public_key
from database.notes import get_aes_key
from cipher.encrypting import encrypt_aes_key
from cipher.decrypting import decrypt_aes_key, get_private_key
from secure.tokens import JWT, CSRF


router = APIRouter(prefix="/accesses", tags=["Accesses"])


@router.post("/set-permission",
             summary="Set permission to your notes",
             description="Set permissions to your notes to be shared other users")
async def set_permission(access: AccessSchema,
                         permission: PermissionSchema = PermissionSchema.read,
                         curr_user: dict = Depends(JWT.get_current_user),
                         _ = Depends(CSRF.verify_csrf_token)) -> dict:

    curr_user_id = curr_user["id"]
    curr_user_name = curr_user["username"]
    if curr_user_id == access.user_id:  # If user enters his id
        return { "message": "You can't give access to yourself!" }

    public_key = get_public_key(access.user_id)  # Public key of user who is gaining access
    private_key = get_private_key(curr_user_name)  # Private key user who sharing note

    aes_key = base64.b64decode(get_aes_key(access.note_id, curr_user_id))  # AES key for this note
    decrypted_aes_key = decrypt_aes_key(private_key, aes_key)  # Decrypted aes_key
    encrypted_aes_key = encrypt_aes_key(public_key, decrypted_aes_key)  # Encrypted aes_key

    permission_value = 1 if permission == PermissionSchema.read else 2
    access = AccessInternalSchema(**access.dict(), key=base64.b64encode(encrypted_aes_key), permission=permission_value)

    return db.set_permission(access, curr_user_id)


@router.patch("/edit-permission",
            summary="Edit permission",
            description="Edit permission for special user to your note")
async def edit_permission(access: AccessSchema,
                          permission: PermissionSchema = PermissionSchema.read,
                          curr_user: dict = Depends(JWT.get_current_user),
                          _ = Depends(CSRF.verify_csrf_token)) -> dict:
    curr_user_id = curr_user["id"]
    if curr_user_id == access.user_id:  # If user enters his id
        return {"message": "You can't change permission to yourself!"}

    permission_value = 1 if permission == PermissionSchema.read else 2
    access = AccessInternalSchema(**access.dict(), key=None, permission=permission_value)

    return db.edit_permission(access, curr_user_id)


@router.delete("/delete-permission",
               summary="Delete permission to your notes",
               description="Delete permission to your notes to be shared other users")
async def delete_permission(access: AccessSchema,
                            curr_user: dict = Depends(JWT.get_current_user),
                            _ = Depends(CSRF.verify_csrf_token)) -> dict:

    curr_user_id = curr_user["id"]
    if curr_user_id == access.user_id:  # If user enters his id
        return { "message": "You can't take access away from yourself!" }

    return db.delete_permission(access, curr_user_id)
