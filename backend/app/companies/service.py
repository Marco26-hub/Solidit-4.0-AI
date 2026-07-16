from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from app.common.security import hash_password
from app.companies.schemas import AuthorizationCreate, CompanyUpdate, MemberCreate
from app.db.models import Company, CompanyMembership, OperatorAuthorization, User


async def get_company(session: AsyncSession, company_id: uuid.UUID) -> Company:
    company = (
        await session.execute(select(Company).where(Company.id == company_id))
    ).scalar_one_or_none()
    if company is None:
        # Either it doesn't exist or RLS hid it — same opaque error either way.
        raise NotFoundError("Company not found")
    return company


async def update_company(
    session: AsyncSession, company_id: uuid.UUID, data: CompanyUpdate
) -> Company:
    company = await get_company(session, company_id)
    if data.name is not None:
        company.name = data.name
    if data.vat_number is not None:
        company.vat_number = data.vat_number
    if data.settings is not None:
        company.settings = data.settings
    if data.active_departments is not None:
        company.active_departments = data.active_departments
    await session.flush()
    return company


def ensure_same_company(token_company_id: uuid.UUID, path_company_id: uuid.UUID) -> None:
    if token_company_id != path_company_id:
        raise ForbiddenError("Token is not scoped to this company")


# ── Team members ──────────────────────────────────────────────────────────────
# The operator→admin approval flow needs real member accounts. Memberships are
# FORCE-RLS tenant rows; users are global (no RLS) — an existing email gets
# ATTACHED to this company, a new one gets created with the given password.


async def list_members(session: AsyncSession, company_id: uuid.UUID) -> list[dict]:
    rows = (
        await session.execute(
            select(CompanyMembership, User)
            .join(User, User.id == CompanyMembership.user_id)
            .where(CompanyMembership.company_id == company_id)
            .order_by(CompanyMembership.created_at)
        )
    ).all()
    return [
        {
            "user_id": m.user_id,
            "email": u.email,
            "full_name": u.full_name,
            "role": m.role,
            "created_at": m.created_at,
        }
        for m, u in rows
    ]


async def add_member(
    session: AsyncSession, company_id: uuid.UUID, data: MemberCreate
) -> dict:
    email = data.email.strip().lower()
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        user = User(
            email=email, password_hash=hash_password(data.password), full_name=data.full_name
        )
        session.add(user)
        await session.flush()
    else:
        existing = (
            await session.execute(
                select(CompanyMembership).where(
                    CompanyMembership.company_id == company_id,
                    CompanyMembership.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ConflictError("Questo utente è già membro dell'azienda.")

    membership = CompanyMembership(company_id=company_id, user_id=user.id, role=data.role)
    session.add(membership)
    await session.flush()
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": membership.role,
        "created_at": membership.created_at,
    }


async def remove_member(
    session: AsyncSession, company_id: uuid.UUID, user_id: uuid.UUID, acting_user_id: uuid.UUID
) -> None:
    if user_id == acting_user_id:
        raise AppError("Non puoi rimuovere te stesso.", code="cannot_remove_self")
    membership = (
        await session.execute(
            select(CompanyMembership).where(
                CompanyMembership.company_id == company_id,
                CompanyMembership.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if membership is None:
        raise NotFoundError("Membro non trovato")
    if membership.role == "company_admin":
        admins = (
            await session.execute(
                select(CompanyMembership).where(
                    CompanyMembership.company_id == company_id,
                    CompanyMembership.role == "company_admin",
                )
            )
        ).scalars().all()
        if len(admins) <= 1:
            raise AppError(
                "Impossibile rimuovere l'ultimo amministratore.", code="last_admin"
            )
    await session.delete(membership)
    await session.flush()


# ── Operator authorizations (ISO/IEC 17025 §6.2 personnel register) ───────────


def _today() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


async def check_operator_authorization(
    session: AsyncSession, company_id: uuid.UUID, user_id: uuid.UUID, method_code: str | None
) -> tuple[bool, str]:
    """True if the operator holds an ACTIVE, in-validity authorisation covering the
    method (a NULL method_code row = authorised for all methods)."""
    today = _today()
    rows = (
        (
            await session.execute(
                select(OperatorAuthorization).where(
                    OperatorAuthorization.company_id == company_id,
                    OperatorAuthorization.user_id == user_id,
                    OperatorAuthorization.status == "active",
                )
            )
        )
        .scalars()
        .all()
    )
    for a in rows:
        if a.valid_from and a.valid_from > today:
            continue
        if a.valid_until and a.valid_until < today:
            continue
        if a.method_code is None or (method_code and a.method_code == method_code):
            scope = a.method_code or "tutti i metodi"
            return True, f"autorizzazione attiva ({scope})"
    return False, (
        f"operatore senza autorizzazione registrata per il metodo {method_code or 'n/d'} "
        "(registro personale ISO 17025 §6.2)"
    )


async def list_authorizations(session: AsyncSession, company_id: uuid.UUID) -> list[dict]:
    rows = (
        await session.execute(
            select(OperatorAuthorization, User)
            .join(User, User.id == OperatorAuthorization.user_id)
            .where(OperatorAuthorization.company_id == company_id)
            .order_by(OperatorAuthorization.created_at.desc())
        )
    ).all()
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "email": u.email,
            "method_code": a.method_code,
            "valid_from": a.valid_from,
            "valid_until": a.valid_until,
            "training_notes": a.training_notes,
            "status": a.status,
        }
        for a, u in rows
    ]


async def add_authorization(
    session: AsyncSession,
    company_id: uuid.UUID,
    data: AuthorizationCreate,
    authorized_by: uuid.UUID,
) -> dict:
    # the target must be a member of this company
    member = (
        await session.execute(
            select(CompanyMembership).where(
                CompanyMembership.company_id == company_id,
                CompanyMembership.user_id == data.user_id,
            )
        )
    ).scalar_one_or_none()
    if member is None:
        raise NotFoundError("L'utente non è membro dell'azienda")
    auth = OperatorAuthorization(
        company_id=company_id,
        user_id=data.user_id,
        method_code=data.method_code,
        authorized_by=authorized_by,
        valid_until=data.valid_until,
        training_notes=data.training_notes,
    )
    session.add(auth)
    await session.flush()
    user = (await session.execute(select(User).where(User.id == data.user_id))).scalar_one()
    return {
        "id": auth.id,
        "user_id": auth.user_id,
        "email": user.email,
        "method_code": auth.method_code,
        "valid_from": auth.valid_from,
        "valid_until": auth.valid_until,
        "training_notes": auth.training_notes,
        "status": auth.status,
    }


async def revoke_authorization(
    session: AsyncSession, company_id: uuid.UUID, auth_id: uuid.UUID
) -> None:
    auth = (
        await session.execute(
            select(OperatorAuthorization).where(
                OperatorAuthorization.id == auth_id,
                OperatorAuthorization.company_id == company_id,
            )
        )
    ).scalar_one_or_none()
    if auth is None:
        raise NotFoundError("Autorizzazione non trovata")
    auth.status = "revoked"
    await session.flush()
