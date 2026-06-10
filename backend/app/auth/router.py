from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.auth import service
from app.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    SelectCompanyRequest,
    TokenResponse,
)
from app.common.deps import Principal, get_principal
from app.common.ratelimit import rate_limit
from app.common.schemas import Message

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# brute-force / abuse guards (per client IP)
_LOGIN_LIMIT = Depends(rate_limit(limit=10, window_seconds=60, scope="login"))
_REGISTER_LIMIT = Depends(rate_limit(limit=5, window_seconds=300, scope="register"))


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[_REGISTER_LIMIT],
)
async def register(payload: RegisterRequest) -> TokenResponse:
    return await service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        company_name=payload.company_name,
        vat_number=payload.vat_number,
    )


@router.post("/login", response_model=TokenResponse, dependencies=[_LOGIN_LIMIT])
async def login(payload: LoginRequest) -> TokenResponse:
    return await service.login(
        email=payload.email, password=payload.password, company_id=payload.company_id
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest) -> TokenResponse:
    return await service.refresh(refresh_token=payload.refresh_token, company_id=payload.company_id)


@router.post("/select-company", response_model=TokenResponse)
async def select_company(
    payload: SelectCompanyRequest, principal: Principal = Depends(get_principal)
) -> TokenResponse:
    return await service.select_company(user_id=principal.user_id, company_id=payload.company_id)


@router.post("/logout", response_model=Message)
async def logout(payload: LogoutRequest) -> Message:
    await service.logout(refresh_token=payload.refresh_token)
    return Message(message="Logged out; refresh-token family revoked.")
