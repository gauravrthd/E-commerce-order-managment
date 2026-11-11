from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/check")
def check_auth():
    return {"message": "Auth router working"}