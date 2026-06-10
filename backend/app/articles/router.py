from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles import service
from app.articles.schemas import (
    ArticleCreate,
    ArticleOut,
    GradingProfileOut,
    VariantCreate,
    VariantOut,
)
from app.common.audit import record_audit
from app.common.deps import Principal, get_db, get_tenant_principal, require_role

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])

_MANAGE = require_role("company_admin", "lab_manager")


@router.post("", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
async def create_article(
    data: ArticleCreate,
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> ArticleOut:
    article = await service.create_article(session, principal.company_id, data)
    await record_audit(
        session,
        action="article.created",
        entity_type="article",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=article.id,
        payload={"code": article.code},
    )
    return ArticleOut.model_validate(article)


@router.get("", response_model=list[ArticleOut])
async def list_articles(
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ArticleOut]:
    articles = await service.list_articles(session, principal.company_id)
    return [ArticleOut.model_validate(a) for a in articles]


# NOTE: declared BEFORE /{article_id} so "grading-profiles" is not captured as a UUID path param.
@router.get("/grading-profiles", response_model=list[GradingProfileOut])
async def list_grading_profiles(
    standard_family: str | None = Query(default=None),
    assessment_type: str | None = Query(default=None),
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> list[GradingProfileOut]:
    profiles = await service.list_grading_profiles(
        session,
        principal.company_id,
        standard_family=standard_family,
        assessment_type=assessment_type,
    )
    return [GradingProfileOut.model_validate(p) for p in profiles]


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(
    article_id: uuid.UUID,
    principal: Principal = Depends(get_tenant_principal),
    session: AsyncSession = Depends(get_db),
) -> ArticleOut:
    article = await service.get_article(session, principal.company_id, article_id)
    return ArticleOut.model_validate(article)


@router.post(
    "/{article_id}/variants",
    response_model=VariantOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_variant(
    article_id: uuid.UUID,
    data: VariantCreate,
    principal: Principal = Depends(_MANAGE),
    session: AsyncSession = Depends(get_db),
) -> VariantOut:
    variant = await service.add_variant(session, principal.company_id, article_id, data)
    await record_audit(
        session,
        action="article.variant_added",
        entity_type="article_variant",
        company_id=principal.company_id,
        actor_user_id=principal.user_id,
        entity_id=variant.id,
        payload={"article_id": str(article_id), "code": variant.code},
    )
    return VariantOut.model_validate(variant)
