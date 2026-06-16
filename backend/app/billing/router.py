from __future__ import annotations

import uuid
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing import service
from app.common.deps import Principal, get_db, get_tenant_principal, require_role
from app.config import settings
from app.db.models import Subscription

router = APIRouter(prefix="/api/v1", tags=["billing"])
logger = structlog.get_logger(__name__)

_BILLING_ADMIN = require_role("company_admin")


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan: str
    status: str
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    current_period_end: datetime | None
    created_at: datetime


class CheckoutIn(BaseModel):
    plan: str = Field(pattern="^(trace|vision)$")


class CheckoutOut(BaseModel):
    url: str


@router.get("/subscriptions", response_model=list[SubscriptionOut])
async def list_subscriptions(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[SubscriptionOut]:
    rows = (
        (
            await session.execute(
                select(Subscription).where(Subscription.company_id == principal.company_id)
            )
        )
        .scalars()
        .all()
    )
    return [SubscriptionOut.model_validate(s) for s in rows]


@router.post("/billing/checkout", response_model=CheckoutOut)
async def create_checkout(
    body: CheckoutIn,
    principal: Principal = Depends(_BILLING_ADMIN),
    session: AsyncSession = Depends(get_db),
) -> CheckoutOut:
    """Create a Stripe Checkout session for the company; returns the redirect URL."""
    url = await service.create_checkout(session, principal.company_id, body.plan)
    return CheckoutOut(url=url)


@router.post("/billing/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> dict:
    """Stripe webhook: verify the signature, then upsert subscription + plan tier.
    No-op until STRIPE_WEBHOOK_SECRET is configured."""
    if not settings.stripe_webhook_secret:
        return {"status": "ignored", "reason": "stripe not configured"}
    payload = await request.body()
    try:
        event = service.verify_event(payload, stripe_signature)
    except Exception as exc:  # noqa: BLE001 - signature/parse errors -> 400
        logger.warning("stripe_webhook_invalid", error=str(exc))
        from app.common.errors import AppError

        raise AppError("Webhook non valido.", code="invalid_webhook") from exc

    # webhook runs without a tenant principal -> open a plain session for the upsert
    from app.db.session import SessionLocal

    async with SessionLocal() as s, s.begin():
        action = await service.apply_event(s, event)
    return {"status": "ok", "action": action}
