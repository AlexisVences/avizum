from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter(prefix="/api/v1")


@router.get("/health/ready")
def ready(db: DbSession) -> JSONResponse:
    """Readiness: the database answers. The body is generic on purpose (no exception text, no versions)."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "unavailable"}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    return JSONResponse({"status": "ready"})
