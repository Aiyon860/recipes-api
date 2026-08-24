import math

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select
from sqlmodel import delete as SQLDelete
from sqlmodel import update as SQLUpdate

from src.db import SessionDep
from src.models import Ingredient, Recipe, RecipeTag, Tag
from src.schemas import (
    IngredientOut,
    RecipeCreate,
    RecipeIndexResponse,
    RecipeListItem,
    RecipeRead,
    RecipeShowResponse,
    RecipeUpdate,
)

router = APIRouter(prefix="/recipes", tags=["Recipes"])

@router.get("", response_model=RecipeIndexResponse)
def index(
    session: SessionDep,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    tag: str | None = None,
    search: str | None = None,
):
    # Filters
    filters = []
    if tag:
        filters.append(
            col(Recipe.id).in_(
                select(RecipeTag.recipe_id)
                .join(Tag, Tag.id == RecipeTag.tag_id)
                .where(Tag.name == tag)
            )
        )
    if search:
        filters.append(col(Recipe.name).ilike(f"%{search}%"))

    # Pagination Metadata
    count_stmt = select(func.count(Recipe.id)).where(*filters)
    total = session.exec(count_stmt).one()
    pages = math.ceil(total / size)
    offset = (page - 1) * size

    # Main Execution
    main_stmt = (
        select(Recipe)
        .options(selectinload(Recipe.recipe_tags))
        .where(*filters)
        .offset(offset)
        .limit(size)
    )
    result = session.exec(main_stmt).all()

    # List of Recipes
    recipes = [
        RecipeListItem(
            id=recipe.id,
            name=recipe.name,
            difficulty=recipe.difficulty,
            servings=recipe.servings,
            total_min=recipe.prep_minutes + recipe.cook_minutes,
            tag_count=len(recipe.recipe_tags)
        )
        for recipe in result
    ]

    return RecipeIndexResponse(
        success=True,
        page=page,
        size=size,
        total=total,
        pages=pages,
        tag=tag,
        search=search,
        data=recipes
    )

@router.post("", status_code=status.HTTP_201_CREATED)
def store(recipe: RecipeCreate, session: SessionDep):
    # Atomic Transaction with Auto Commit
    with session.begin():
        # Add Recipe
        try:
            new_recipe = Recipe(
                **recipe.model_dump(exclude={"ingredients", "tags"})
            )
            session.add(new_recipe)
            session.flush()
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Recipe with name '{recipe.name}' already exists."
            )

        # Add Ingredients
        new_ingredients = [
            Ingredient(
                **ingredient.model_dump(),
                recipe_id=new_recipe.id,
                position=idx
            )
            for idx, ingredient in enumerate(recipe.ingredients)
        ]
        session.add_all(new_ingredients)

        # Add Tags
        session.exec(
            insert(Tag)
                .values([{"name": tag} for tag in recipe.tags])
                .on_conflict_do_nothing(index_elements=["name"])
        )
        new_tags = session.exec(
            select(Tag)
                .where(col(Tag.name).in_(recipe.tags))
        ).all()

        # Add Recipe Tags (pivot table)
        new_recipe_tags = [RecipeTag(tag_id=tag.id, recipe_id=new_recipe.id) for tag in new_tags]
        session.add_all(new_recipe_tags)

    session.refresh(new_recipe)

    return RecipeShowResponse(
        success=True,
        data=RecipeRead(
            **new_recipe.model_dump(exclude={"ingredients", "tags"}),
            ingredients=[
                IngredientOut(**ingredient.model_dump())
                for ingredient in new_ingredients
            ],
            tags=[tag.name for tag in new_tags]
        )
    )

@router.get("/{id}", response_model=RecipeShowResponse)
def show(session: SessionDep, id: int):
    stmt = select(Recipe).options(selectinload(Recipe.recipe_tags).options(selectinload(RecipeTag.tag))).options(selectinload(Recipe.ingredients)).where(Recipe.id == id)
    recipe = session.exec(stmt).first()
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id={id} is not found."
        )

    tags = [rt.tag.name for rt in recipe.recipe_tags]
    ingredients = [
        IngredientOut(**ingredient.model_dump(exclude={"recipe_id", "created_at", "updated_at"}))
        for ingredient in recipe.ingredients
    ]

    return RecipeShowResponse(
        success=True,
        data=RecipeRead(
            **recipe.model_dump(),
            tags=tags,
            ingredients=ingredients
        )
    )

@router.api_route("/{id}", methods=["PUT", "PATCH"])
def update(session: SessionDep, id: int, payload: RecipeUpdate):
    with session.begin():
        stmt = select(Recipe).options(selectinload(Recipe.recipe_tags).options(selectinload(RecipeTag.tag))).options(selectinload(Recipe.ingredients)).where(Recipe.id == id)
        recipe = session.exec(stmt).first()
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with id={id} is not found."
            )

        recipe_data = recipe.model_dump(exclude={"ingredients", "tags"})
        ingredients = recipe.ingredients
        tags = [rt.tag.name for rt in recipe.recipe_tags]

        tags_payload = payload.tags
        if tags_payload is not None:
            # Delete associated RecipeTags
            stmt = SQLDelete(RecipeTag).where(col(RecipeTag.recipe_id) == recipe.id)
            session.exec(stmt)

            # Add Tags if any
            if len(tags_payload) > 0:
                stmt = insert(Tag).values([{"name": tag} for tag in tags_payload]).on_conflict_do_nothing(index_elements=["name"])
                session.exec(stmt)

                stmt = select(Tag.id).where(col(Tag.name).in_(tags_payload))
                tag_ids = session.exec(stmt).all()

                # Add Recipe Tags (pivot table)
                new_recipe_tags = [RecipeTag(tag_id=tag_id, recipe_id=recipe.id) for tag_id in tag_ids]
                session.add_all(new_recipe_tags)

            tags = tags_payload

        ingredients_payload = payload.ingredients
        if ingredients_payload is not None:
            # Delete associated ingredients
            stmt = SQLDelete(Ingredient).where(Ingredient.recipe_id == recipe.id)
            session.exec(stmt)

            # Add Ingredients if any
            if len(ingredients_payload) > 0:
                ingredients = [
                    Ingredient(
                        **ingredient.model_dump(),
                        position=pos,
                        recipe_id=recipe.id
                    )
                    for pos, ingredient in enumerate(ingredients_payload)
                ]
                session.add_all(ingredients)
                session.flush()
            else:
                ingredients = []

        # Update Recipe
        recipe_payload = payload.model_dump(exclude_unset=True, exclude={"ingredients", "tags"})
        if recipe_payload:
            stmt = SQLUpdate(Recipe).where(Recipe.id == recipe.id).values(**recipe_payload)
            session.exec(stmt)
        for key, value in recipe_payload.items():
            recipe_data[key] = value

    return RecipeShowResponse(
        success=True,
        data=RecipeRead(
            **recipe_data,
            ingredients=[
                IngredientOut(**ingredient.model_dump(exclude={"created_at", "updated_at"}))
                for ingredient in ingredients
            ],
            tags=tags
        )
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(session: SessionDep, id: int):
    with session.begin():
        stmt = select(Recipe).where(Recipe.id == id)

        recipe = session.exec(stmt).first()
        if not recipe:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with id={id} is not found."
            )

        session.delete(recipe)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
