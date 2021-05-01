from fastapi import APIRouter

from app import __version__

api_router = APIRouter()

@api_router.get("/", response_model=schemas.Msg, status_code=200)
def root() -> dict:
    """
    Root Get
    """
    return {"msg": "This is the Example API"}


@api_router.get("/health", response_model=schemas.Health, status_code=200)
def health() -> dict:
    """
    Root Get
    """
    return {"name": "Example API", "version": __version__}
