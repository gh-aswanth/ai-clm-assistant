"""HTTP API for CPWD-style contract review guideline bundles."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import re

from app.db.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter(prefix="/guidelines", tags=["guidelines"])


@router.get("/frameworks", response_model=list[schemas.GuidelineFrameworkSchema])
def list_guideline_frameworks(db: Session = Depends(get_db)):
    return (
        db.query(models.GuidelineFramework)
        .order_by(models.GuidelineFramework.id.asc())
        .all()
    )


@router.post("/frameworks", response_model=schemas.GuidelineFrameworkSchema, status_code=201)
def create_guideline_framework(body: schemas.GuidelineFrameworkCreate, db: Session = Depends(get_db)):
    slug = re.sub(r"[^a-z0-9-]", "-", body.slug.lower().strip()).strip("-")
    existing = db.query(models.GuidelineFramework).filter(models.GuidelineFramework.slug == slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="A framework with this slug already exists")
    if body.is_default:
        db.query(models.GuidelineFramework).update({models.GuidelineFramework.is_default: False})
    fw = models.GuidelineFramework(
        slug=slug, title=body.title, summary=body.summary,
        version_label=body.version_label, is_default=body.is_default,
    )
    db.add(fw)
    db.commit()
    db.refresh(fw)
    return fw


@router.patch("/frameworks/{slug}", response_model=schemas.GuidelineFrameworkSchema)
def update_guideline_framework(slug: str, body: schemas.GuidelineFrameworkUpdate, db: Session = Depends(get_db)):
    fw = db.query(models.GuidelineFramework).filter(models.GuidelineFramework.slug == slug).first()
    if not fw:
        raise HTTPException(status_code=404, detail="Guideline framework not found")
    if body.is_default is True:
        db.query(models.GuidelineFramework).filter(models.GuidelineFramework.id != fw.id).update(
            {models.GuidelineFramework.is_default: False}
        )
    for field in ("title", "summary", "version_label", "is_default"):
        val = getattr(body, field, None)
        if val is not None:
            setattr(fw, field, val)
    db.commit()
    db.refresh(fw)
    return fw


@router.delete("/frameworks/{slug}", status_code=204)
def delete_guideline_framework(slug: str, db: Session = Depends(get_db)):
    fw = db.query(models.GuidelineFramework).filter(models.GuidelineFramework.slug == slug).first()
    if not fw:
        raise HTTPException(status_code=404, detail="Guideline framework not found")
    db.delete(fw)
    db.commit()


@router.get("/frameworks/{slug}", response_model=schemas.GuidelineFrameworkSchema)
def get_guideline_framework(slug: str, db: Session = Depends(get_db)):
    fw = (
        db.query(models.GuidelineFramework)
        .filter(models.GuidelineFramework.slug == slug)
        .first()
    )
    if not fw:
        raise HTTPException(status_code=404, detail="Guideline framework not found")
    return fw


@router.get("/frameworks/{slug}/bundle", response_model=schemas.GuidelineBundleSchema)
def get_guideline_bundle(slug: str, db: Session = Depends(get_db)):
    fw = (
        db.query(models.GuidelineFramework)
        .filter(models.GuidelineFramework.slug == slug)
        .first()
    )
    if not fw:
        raise HTTPException(status_code=404, detail="Guideline framework not found")
    sections = (
        db.query(models.GuidelineSection)
        .filter(models.GuidelineSection.framework_id == fw.id)
        .order_by(models.GuidelineSection.sort_order.asc(), models.GuidelineSection.id.asc())
        .all()
    )
    catalog = (
        db.query(models.GuidelineCatalogEntry)
        .filter(models.GuidelineCatalogEntry.framework_id == fw.id)
        .order_by(
            models.GuidelineCatalogEntry.bucket.asc(),
            models.GuidelineCatalogEntry.domain.asc(),
            models.GuidelineCatalogEntry.sort_order.asc(),
        )
        .all()
    )
    return schemas.GuidelineBundleSchema(framework=fw, sections=sections, catalog=catalog)


@router.get(
    "/frameworks/{slug}/views/section-index",
    response_model=list[schemas.GuidelineSectionIndexRow],
)
def get_section_index_view(slug: str, db: Session = Depends(get_db)):
    """Read-only access to v_guideline_section_index (database view)."""
    try:
        rows = db.execute(
            text(
                """
                SELECT v.framework_id, v.framework_slug, v.framework_title,
                       v.section_id, v.section_key, v.section_title, v.sort_order
                FROM v_guideline_section_index v
                WHERE v.framework_slug = :slug
                ORDER BY v.sort_order, v.section_id
                """
            ),
            {"slug": slug},
        ).mappings().all()
    except OperationalError as exc:
        if "no such table: v_guideline_section_index" in str(exc):
            rows = [
                {
                    "framework_id": fw.id,
                    "framework_slug": fw.slug,
                    "framework_title": fw.title,
                    "section_id": sec.id,
                    "section_key": sec.section_key,
                    "section_title": sec.title,
                    "sort_order": sec.sort_order,
                }
                for fw, sec in db.query(models.GuidelineFramework, models.GuidelineSection)
                .join(
                    models.GuidelineSection,
                    models.GuidelineSection.framework_id == models.GuidelineFramework.id,
                )
                .filter(models.GuidelineFramework.slug == slug)
                .order_by(models.GuidelineSection.sort_order.asc(), models.GuidelineSection.id.asc())
                .all()
            ]
        else:
            raise

    if not rows:
        exists = (
            db.query(models.GuidelineFramework.id)
            .filter(models.GuidelineFramework.slug == slug)
            .first()
        )
        if not exists:
            raise HTTPException(status_code=404, detail="Guideline framework not found")
    return [schemas.GuidelineSectionIndexRow(**dict(r)) for r in rows]


# ── Section CRUD ──────────────────────────────────────────────────────────────

def _get_fw(slug: str, db: Session):
    fw = db.query(models.GuidelineFramework).filter(models.GuidelineFramework.slug == slug).first()
    if not fw:
        raise HTTPException(status_code=404, detail="Guideline framework not found")
    return fw


@router.post("/frameworks/{slug}/sections", response_model=schemas.GuidelineSectionSchema, status_code=201)
def create_section(slug: str, body: schemas.GuidelineSectionCreate, db: Session = Depends(get_db)):
    fw = _get_fw(slug, db)
    dupe = db.query(models.GuidelineSection).filter(
        models.GuidelineSection.framework_id == fw.id,
        models.GuidelineSection.section_key == body.section_key,
    ).first()
    if dupe:
        raise HTTPException(status_code=409, detail="Section key already exists in this framework")
    sec = models.GuidelineSection(
        framework_id=fw.id, section_key=body.section_key,
        title=body.title, sort_order=body.sort_order, body=body.body or {},
    )
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return sec


@router.patch("/frameworks/{slug}/sections/{section_id}", response_model=schemas.GuidelineSectionSchema)
def update_section(slug: str, section_id: int, body: schemas.GuidelineSectionUpdate, db: Session = Depends(get_db)):
    fw = _get_fw(slug, db)
    sec = db.query(models.GuidelineSection).filter(
        models.GuidelineSection.id == section_id,
        models.GuidelineSection.framework_id == fw.id,
    ).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found")
    if body.title is not None:
        sec.title = body.title
    if body.sort_order is not None:
        sec.sort_order = body.sort_order
    if body.body is not None:
        sec.body = body.body
    db.commit()
    db.refresh(sec)
    return sec


@router.delete("/frameworks/{slug}/sections/{section_id}", status_code=204)
def delete_section(slug: str, section_id: int, db: Session = Depends(get_db)):
    fw = _get_fw(slug, db)
    sec = db.query(models.GuidelineSection).filter(
        models.GuidelineSection.id == section_id,
        models.GuidelineSection.framework_id == fw.id,
    ).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found")
    db.delete(sec)
    db.commit()
