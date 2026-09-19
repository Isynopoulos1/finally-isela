"""Health check for Docker / deployment."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def get_health(request: Request):
    return {"status": "ok", "market_provider": request.app.state.provider.name}
