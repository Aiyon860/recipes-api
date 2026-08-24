# Pydantic Models (API)

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import ConfigDict
from sqlmodel import Field, SQLModel

from src.enums import DifficultyEnum


class IngredientIn(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    unit: str = Field(min_length=1)

class IngredientOut(SQLModel):
    id: int
    name: str
    quantity: Decimal
    unit: str
    position: int

class StepIn(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    number: int = Field(gt=0)
    text: str = Field(min_length=1)

class StepOut(SQLModel):
    number: int
    text: str

class TagCreate(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)

class TagRead(SQLModel):
    name: str
    recipe_count: int

class RecipeCreate(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    description: str | None = Field(default=None)
    servings: int = Field(default=1, gt=0)

    prep_minutes: int = Field(default=0, ge=0)
    cook_minutes: int = Field(default=0, ge=0)
    difficulty: DifficultyEnum | None = Field(default=None)

    ingredients: list[IngredientIn]
    instruction_steps: list[StepIn]
    tags: list[str]

class RecipeUpdate(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None)
    servings: int | None = Field(default=None, gt=0)

    prep_minutes: int | None = Field(default=None, ge=0)
    cook_minutes: int | None = Field(default=None, ge=0)
    difficulty: DifficultyEnum | None = Field(default=None)

    ingredients: list[IngredientIn] | None = Field(default=None)
    instruction_steps: list[StepIn] | None = Field(default=None)
    tags: list[str] | None = Field(default=None)

class RecipeRead(SQLModel):
    id: int
    name: str
    description: str | None
    servings: int
    prep_minutes: int
    cook_minutes: int
    difficulty: DifficultyEnum | None

    instruction_steps: list[StepOut]
    tags: list[str]
    ingredients: list[IngredientOut]

    created_at: datetime
    updated_at: datetime

class RecipeListItem(SQLModel):
    id: int
    name: str
    difficulty: DifficultyEnum | None
    servings: int

    # computed fields
    total_min: int      # prep_minutes + cook_minutes
    tag_count: int

# API
class GenericResponse(SQLModel):
    success: bool
    message: str | None = None
    data: Any | None = None
    error: str | None = None

class RecipeIndexResponse(GenericResponse):
    page: int
    size: int
    total: int
    pages: int
    tag: str | None = None
    search: str | None = None
    data: list[RecipeListItem]

class RecipeShowResponse(GenericResponse):
    data: RecipeRead
