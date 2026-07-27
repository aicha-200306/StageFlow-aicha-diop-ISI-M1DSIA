from fastapi import APIRouter, Depends
from app.dependencies.permissions import get_current_user_payload

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def read_current_user(payload: dict = Depends(get_current_user_payload)):
    return {"id": payload["sub"], "role": payload["role"]}