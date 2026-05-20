from fastapi import APIRouter
import httpx

from backend.app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/llm/health")
async def llm_health_check() -> dict[str, str]:
    models_url = f"{settings.llm_api_base_url.rstrip('/')}/models"

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                models_url,
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return {
            "status": "unavailable",
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "detail": str(exc),
        }

    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "model": settings.llm_model,
    }
