from datetime import datetime
from decimal import Decimal

from sqlmodel import JSON, Column, DateTime, Field, Relationship, SQLModel

from src.enums import DifficultyEnum
from src.helper import utc_now


class Recipe(SQLModel, table=True):
    __tablename__ = "t_recipes"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = Field(default=None)
    servings: int = Field(default=1, gt=0)

    prep_minutes: int = Field(default=0, ge=0)
    cook_minutes: int = Field(default=0, ge=0)

    difficulty: DifficultyEnum | None = Field(default=None)
    instruction_steps: list[dict] = Field(default_factory=list, sa_column=Column(JSON))

    ingredients: list["Ingredient"] = Relationship(
        back_populates="recipe", cascade_delete=True,
        sa_relationship_kwargs={"order_by": "Ingredient.position"}
    )
    recipe_tags: list["RecipeTag"] = Relationship(back_populates="recipe", cascade_delete=True)

    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), onupdate=utc_now))


class Ingredient(SQLModel, table=True):
    __tablename__ = "t_ingredients"

    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(index=True)
    quantity: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    unit: str = Field(min_length=1)
    position: int = Field(ge=0)

    recipe_id: int = Field(foreign_key="t_recipes.id", ondelete="CASCADE")

    recipe: Recipe = Relationship(back_populates="ingredients")

    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), onupdate=utc_now))


class Tag(SQLModel, table=True):
    __tablename__ = "t_tags"

    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(unique=True, index=True, min_length=1, max_length=50)

    recipe_tags: list["RecipeTag"] = Relationship(back_populates="tag", cascade_delete=True)


class RecipeTag(SQLModel, table=True):
    __tablename__ = "t_recipe_tags"

    id: int | None = Field(primary_key=True, default=None)
    recipe_id: int = Field(foreign_key="t_recipes.id", ondelete="CASCADE")
    tag_id: int = Field(foreign_key="t_tags.id", ondelete="CASCADE")

    recipe: Recipe = Relationship(back_populates="recipe_tags")
    tag: Tag = Relationship(back_populates="recipe_tags")
