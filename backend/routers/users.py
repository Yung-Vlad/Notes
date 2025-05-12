from fastapi import APIRouter, HTTPException, status
from fastapi import Request
from notes_api.routers import users  # Assuming this function checks if a user is logged in


router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/check-session", summary="Check if user is logged in")
async def check_session(request: Request) -> dict:
    if users.check_logged(request):  # Use the check_logged function
        return {"status": "success", "message": "User is logged in."}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: No active session."
        )