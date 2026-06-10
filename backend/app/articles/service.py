from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.articles.schemas import ArticleCreate, VariantCreate
from app.common.errors import ConflictError, NotFoundError
from app.db.models import Article, ArticleVariant, GradingProfile


async def _get_article(
    session: AsyncSession, company_id: uuid.UUID, article_id: uuid.UUID
) -> Article:
    row = (
        await session.execute(
            select(Article).where(Article.id == article_id, Article.company_id == company_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Article not found")
    return row


async def create_article(
    session: AsyncSession,
    company_id: uuid.UUID,
    data: ArticleCreate,
) -> Article:
    existing = (
        await session.execute(
            select(Article).where(Article.company_id == company_id, Article.code == data.code)
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(f"Article with code '{data.code}' already exists")

    article = Article(
        company_id=company_id,
        code=data.code,
        name=data.name,
        composition=data.composition,
        brand_specification_id=data.brand_specification_id,
    )
    session.add(article)
    await session.flush()

    for v in data.variants:
        variant = ArticleVariant(
            company_id=company_id,
            article_id=article.id,
            code=v.code,
            color_name=v.color_name,
            lot_code=v.lot_code,
            reference_lab=v.reference_lab.model_dump() if v.reference_lab else None,
        )
        session.add(variant)
    await session.flush()

    # reload with variants for response
    return await get_article(session, company_id, article.id)


async def get_article(
    session: AsyncSession, company_id: uuid.UUID, article_id: uuid.UUID
) -> Article:
    article = await _get_article(session, company_id, article_id)
    # load variants
    variants = list(
        (
            await session.execute(
                select(ArticleVariant)
                .where(
                    ArticleVariant.company_id == company_id,
                    ArticleVariant.article_id == article_id,
                )
                .order_by(ArticleVariant.created_at)
            )
        )
        .scalars()
        .all()
    )
    article.variants = variants  # type: ignore[attr-defined]
    return article


async def list_articles(session: AsyncSession, company_id: uuid.UUID) -> list[Article]:
    rows = list(
        (
            await session.execute(
                select(Article)
                .where(Article.company_id == company_id)
                .order_by(Article.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    for article in rows:
        variants = list(
            (
                await session.execute(
                    select(ArticleVariant)
                    .where(
                        ArticleVariant.company_id == company_id,
                        ArticleVariant.article_id == article.id,
                    )
                    .order_by(ArticleVariant.created_at)
                )
            )
            .scalars()
            .all()
        )
        article.variants = variants  # type: ignore[attr-defined]
    return rows


async def add_variant(
    session: AsyncSession,
    company_id: uuid.UUID,
    article_id: uuid.UUID,
    data: VariantCreate,
) -> ArticleVariant:
    await _get_article(session, company_id, article_id)
    existing = (
        await session.execute(
            select(ArticleVariant).where(
                ArticleVariant.company_id == company_id,
                ArticleVariant.article_id == article_id,
                ArticleVariant.code == data.code,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(f"Variant '{data.code}' already exists on this article")

    variant = ArticleVariant(
        company_id=company_id,
        article_id=article_id,
        code=data.code,
        color_name=data.color_name,
        lot_code=data.lot_code,
        reference_lab=data.reference_lab.model_dump() if data.reference_lab else None,
    )
    session.add(variant)
    await session.flush()
    return variant


async def list_grading_profiles(
    session: AsyncSession,
    company_id: uuid.UUID,
    *,
    standard_family: str | None = None,
    assessment_type: str | None = None,
) -> list[GradingProfile]:
    """Return builtin profiles (company_id IS NULL) + tenant's custom profiles."""
    stmt = select(GradingProfile).where(
        (GradingProfile.company_id == None) | (GradingProfile.company_id == company_id)  # noqa: E711
    )
    if standard_family:
        stmt = stmt.where(GradingProfile.standard_family == standard_family)
    if assessment_type:
        stmt = stmt.where(GradingProfile.assessment_type == assessment_type)
    stmt = stmt.order_by(GradingProfile.is_builtin.desc(), GradingProfile.code)
    return list((await session.execute(stmt)).scalars().all())


async def resolve_grading_profile(
    session: AsyncSession,
    company_id: uuid.UUID,
    *,
    standard_family: str,
    assessment_type: str,
) -> GradingProfile | None:
    """Prefer tenant-custom over builtin; return None if nothing found."""
    profiles = await list_grading_profiles(
        session,
        company_id,
        standard_family=standard_family,
        assessment_type=assessment_type,
    )
    # company-specific first, then builtin
    for p in sorted(profiles, key=lambda p: (p.is_builtin, p.code)):
        return p
    return None
