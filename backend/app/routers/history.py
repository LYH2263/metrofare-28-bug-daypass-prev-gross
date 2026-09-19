from fastapi import APIRouter
from app.services.metro_service import MetroService

router = APIRouter(tags=["history"])

@router.get("/history")
def history(limit: int = 50):
    with MetroService() as s:
        return {"items": s.history(limit)}
