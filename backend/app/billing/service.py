"""Stripe billing: checkout session + webhook → subscription state + plan gating.

Stripe is lazy-imported and only active when STRIPE_SECRET_KEY is set, so the base
app (and tests) run without it. On an active subscription the company's
account_tier is set to the plan, which drives feature gating (billing/deps.py)."""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError
from app.config import settings
from app.db.models import Company, Subscription

# plan -> (Stripe price id, account_tier granted)
_PLANS = {
    "trace": ("stripe_price_trace", "trace"),
    "vision": ("stripe_price_vision", "vision"),
}


def _stripe():
    if not settings.stripe_secret_key:
        raise AppError("Stripe non configurato.", code="stripe_not_configured")
    import stripe

    stripe.api_key = settings.stripe_secret_key
    return stripe


async def _get_or_create_sub(
    session: AsyncSession, company_id: uuid.UUID, plan: str
) -> Subscription:
    sub = (
        await session.execute(select(Subscription).where(Subscription.company_id == company_id))
    ).scalar_one_or_none()
    if sub is None:
        sub = Subscription(company_id=company_id, plan=plan, status="incomplete")
        session.add(sub)
        await session.flush()
    return sub


async def create_checkout(session: AsyncSession, company_id: uuid.UUID, plan: str) -> str:
    """Create a Stripe Checkout session for a plan; return the redirect URL."""
    if plan not in _PLANS:
        raise AppError(f"Piano sconosciuto: {plan}", code="unknown_plan")
    price_attr, _tier = _PLANS[plan]
    price_id = getattr(settings, price_attr, None)
    if not price_id:
        raise AppError(f"Prezzo Stripe non configurato per il piano {plan}.", code="no_price")

    stripe = _stripe()
    company = (await session.execute(select(Company).where(Company.id == company_id))).scalar_one()
    sub = await _get_or_create_sub(session, company_id, plan)

    customer_id = sub.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            name=company.name, metadata={"company_id": str(company_id)}
        )
        customer_id = customer["id"]
        sub.stripe_customer_id = customer_id
        sub.plan = plan
        await session.flush()

    base = settings.web_base_url.rstrip("/")
    cs = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{base}/billing?status=success",
        cancel_url=f"{base}/billing?status=cancel",
        metadata={"company_id": str(company_id), "plan": plan},
    )
    return cs["url"]


def verify_event(payload: bytes, sig_header: str | None) -> dict:
    stripe = _stripe()
    if not settings.stripe_webhook_secret:
        raise AppError("Webhook secret non configurato.", code="no_webhook_secret")
    return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)


def _tier_for_plan(plan: str | None) -> str:
    return _PLANS.get(plan or "", ("", "trace"))[1]


def _resolve_company_id(obj: dict) -> uuid.UUID | None:
    """Company is carried in our metadata (checkout) or on the Stripe customer."""
    meta_cid = (obj.get("metadata") or {}).get("company_id")
    if meta_cid:
        return uuid.UUID(meta_cid)
    customer = obj.get("customer")
    if customer:
        cust = _stripe().Customer.retrieve(customer)
        cid = (cust.get("metadata") or {}).get("company_id")
        if cid:
            return uuid.UUID(cid)
    return None


async def apply_event(session: AsyncSession, event: dict) -> str:
    """Upsert subscription + company tier from a Stripe event. Returns the action.
    The webhook has no tenant principal, so we resolve the company from Stripe and
    set the RLS context before any tenant-scoped read/write."""
    from app.common.rls import apply_rls

    etype = event.get("type", "")
    obj = event.get("data", {}).get("object", {})

    company_id = _resolve_company_id(obj)
    if company_id is None:
        return "ignored_no_company"

    # scope this session to the resolved company so RLS allows the upsert
    await apply_rls(session, user_id=uuid.UUID(int=0), company_id=company_id)

    sub_row = (
        await session.execute(select(Subscription).where(Subscription.company_id == company_id))
    ).scalar_one_or_none()
    if sub_row is None:
        sub_row = Subscription(company_id=company_id, plan="trace", status="incomplete")
        session.add(sub_row)

    company = (
        await session.execute(select(Company).where(Company.id == company_id))
    ).scalar_one_or_none()

    if etype == "checkout.session.completed":
        plan = (obj.get("metadata") or {}).get("plan", sub_row.plan)
        sub_row.plan = plan
        sub_row.status = "active"
        sub_row.stripe_subscription_id = obj.get("subscription")
        if obj.get("customer"):
            sub_row.stripe_customer_id = obj["customer"]
        if company:
            company.account_tier = _tier_for_plan(plan)
    elif etype in ("customer.subscription.updated", "customer.subscription.created"):
        sub_row.status = obj.get("status", sub_row.status)
        sub_row.stripe_subscription_id = obj.get("id")
        end = obj.get("current_period_end")
        if end:
            sub_row.current_period_end = dt.datetime.fromtimestamp(end, tz=dt.UTC)
        if company and sub_row.status in ("active", "trialing"):
            company.account_tier = _tier_for_plan(sub_row.plan)
    elif etype in ("customer.subscription.deleted",):
        sub_row.status = "canceled"
        if company:
            company.account_tier = "trace"
    else:
        return f"ignored:{etype}"

    await session.flush()
    return f"applied:{etype}"
