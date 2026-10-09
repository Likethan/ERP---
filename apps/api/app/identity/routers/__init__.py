"""Aggregation of Enterprise Identity Routers (Step 22)."""

from fastapi import APIRouter

from app.identity.routers.federation import router as federation_router
from app.identity.routers.linking import router as linking_router
from app.identity.routers.mfa import router as mfa_router
from app.identity.routers.policies import router as policies_router
from app.identity.routers.providers import router as providers_router
from app.identity.routers.sessions import router as sessions_router

identity_router = APIRouter(prefix="/identity", tags=["Enterprise Identity"])

identity_router.include_router(providers_router)
identity_router.include_router(sessions_router)
identity_router.include_router(linking_router)
identity_router.include_router(policies_router)
identity_router.include_router(mfa_router)
identity_router.include_router(federation_router)

__all__ = ["identity_router"]
