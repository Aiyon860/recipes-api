import math
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import distinct, func, select

from src.db import SessionDep
from src.models import RecipeTag, Tag
from src.schemas import TagCreate, TagIndexResponse, TagRead, TagShowResponse, TagUpdate

router = APIRouter(prefix="/tags", tags=["v1", "Tags"])


@router.get("", response_model=TagIndexResponse)
def index(
    session: SessionDep,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    order: Literal["asc", "desc"] = Query(default="asc"),
):
    # Metadata
    stmt = select(func.count(Tag.id))
    total = session.exec(stmt).one()
    pages = math.ceil(total / size)
    offset = (page - 1) * size

    # Get all tags
    stmt = (
        select(
            Tag.name,
            func.coalesce(func.count(distinct(RecipeTag.recipe_id)), 0).label(
                "recipe_count"
            ),
        )
        .outerjoin(RecipeTag)
        .group_by(Tag.id)
        .offset(offset)
        .limit(size)
        .order_by(Tag.name.asc() if order == "asc" else Tag.name.desc())
    )
    result = session.exec(stmt).mappings().all()
    tags = [
        TagRead(name=tag["name"], recipe_count=tag["recipe_count"]) for tag in result
    ]

    return TagIndexResponse(
        success=True, data=tags, page=page, size=size, total=total, pages=pages
    )


@router.post("", response_model=TagShowResponse, status_code=status.HTTP_201_CREATED)
def store(tag: TagCreate, session: SessionDep):
    with session.begin():
        new_tag = Tag(**tag.model_dump())
        try:
            session.add(new_tag)
            session.flush()
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{new_tag.name}' already exists.",
            )

    return TagShowResponse(success=True, data=new_tag)


@router.get("/{id}", response_model=TagShowResponse)
def show(id: int, session: SessionDep):
    stmt = select(Tag).where(Tag.id == id)

    tag = session.exec(stmt).first()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id={id} is not found.",
        )

    return TagShowResponse(success=True, data=tag)


@router.api_route("/{id}", methods=["PUT", "PATCH"], response_model=TagShowResponse)
def update(id: int, payload: TagUpdate, session: SessionDep):
    # Auto commit and close conn
    with session.begin():
        stmt = select(Tag).where(Tag.id == id)

        tag = session.exec(stmt).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with id={id} is not found.",
            )

        # Update tag
        try:
            tag.name = payload.name
            session.add(tag)
            session.flush()
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{payload.name}' already exists.",
            )

    return TagShowResponse(success=True, data=tag)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(id: int, session: SessionDep):
    # Auto commit and close conn
    with session.begin():
        stmt = select(Tag).where(Tag.id == id)

        tag = session.exec(stmt).first()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with id={id} is not found.",
            )

        session.delete(tag)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
