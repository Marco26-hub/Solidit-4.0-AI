from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.deps import Principal, get_db, get_tenant_principal
from app.config import settings
from app.db.models import Subscription

router = APIRouter(prefix="/api/v1", tags=["billing"])


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan: str
    status: str
    stripe_customer_id: str | None
    stripe_subscription_id: str | None
    current_period_end: datetime | None
    created_at: datetime


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


@router.post("/billing/webhook")
async def stripe_webhook(request: Request) -> dict:
    """Stripe webhook (skeleton). No-op until STRIPE_WEBHOOK_SECRET is configured.
    TODO (Phase 9): verify the signature with stripe.Webhook.construct_event and
    upsert subscription status on customer.subscription.* events."""
    if not settings.stripe_webhook_secret:
        return {"status": "ignored", "reason": "stripe not configured"}
    _ = await request.body()
    return {"status": "received"}
