"""Aggregate v1 router. Sub-routers are added here as they come online."""
from __future__ import annotations

from fastapi import APIRouter


api_router = APIRouter(prefix="/api/v1")


# Sub-routers are imported lazily inside try/except so the app can boot
# during incremental builds before every module is implemented.
def _safe_include(module: str, router_name: str) -> None:
    import importlib

    try:
        mod = importlib.import_module(module)
        api_router.include_router(getattr(mod, router_name))
    except ModuleNotFoundError:
        # Module not yet implemented in this incremental build.
        pass


_safe_include("app.api.v1.auth", "router")
_safe_include("app.api.v1.users", "router")
_safe_include("app.api.v1.goals", "router")
_safe_include("app.api.v1.resources", "router")
_safe_include("app.api.v1.lessons", "router")
_safe_include("app.api.v1.reviews", "router")
_safe_include("app.api.v1.quizzes", "router")
_safe_include("app.api.v1.dashboard", "router")
_safe_include("app.api.v1.internal", "router")
_safe_include("app.api.v1.internal_ai", "router")
_safe_include("app.api.v1.internal_bot", "router")