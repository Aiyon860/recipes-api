# Pydantic Models (API)

from datetime import datetime
from decimal import Decimal
import re
from typing import Any

from pydantic import ConfigDict, field_serializer, field_validator
from sqlmodel import Field, SQLModel

from src.enums import DifficultyEnum, UserRoleEnum
from src.models import Tag


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

    @field_serializer("quantity")
    def serialize_quantity(self, v: Decimal) -> str:
        return f"{v:.3f}"


class StepIn(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    number: int = Field(gt=0)
    text: str = Field(min_length=1)


class StepOut(SQLModel):
    number: int
    text: str


class TagCreate(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=50)


class TagRead(SQLModel):
    name: str
    recipe_count: int


class TagUpdate(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)


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
    total_min: int  # prep_minutes + cook_minutes
    tag_count: int

class UserCreate(SQLModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
    role: UserRoleEnum = Field()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter.")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")

        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit.")

        if not re.search(r"[ !@#$%^&*(),.?\":{}|<>_+-]", value):
            raise ValueError("Password must contain at least one special character.")

        return value

class UserRead(SQLModel):
    id: int
    username: str
    role: UserRoleEnum

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


class TagIndexResponse(GenericResponse):
    page: int
    size: int
    total: int
    pages: int
    data: list[TagRead]


class TagShowResponse(GenericResponse):
    data: Tag

class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(SQLModel):
    sub: int
    role: UserRoleEnum
    exp: datetime
