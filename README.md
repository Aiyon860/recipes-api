<!-- prettier-ignore -->
<div align="center">

# Recipe Collection API

A RESTful API for managing recipes, built with FastAPI, SQLAlchemy 2.0, and SQLite.

![Python](https://img.shields.io/badge/Python-3.14+-3776ab?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-d71f00?style=flat-square&logo=sqlalchemy&logoColor=white)

[Overview](#overview) • [Quick Start](#quick-start) • [API Endpoints](#api-endpoints) • [Configuration](#configuration) • [Testing](#testing)

</div>

## Overview

A recipe management API with full CRUD operations, nested ingredients, tag-based filtering, and pagination. Built to learn the modern Python web stack — FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync), Alembic, and SQLite.

Key design decisions are documented in [`docs/adr/0001-recipe-collection-data-model.md`](docs/adr/0001-recipe-collection-data-model.md).

## Features

- **Recipe CRUD** — create, read, update (partial PATCH), and delete recipes with cascading ingredient removal
- **Nested ingredients** — ordered list with decimal quantities and free-text units
- **Instruction steps** — JSON-validated ordered steps per recipe
- **Tag management** — many-to-many relationships with recipe count aggregation
- **Filtering & search** — filter by exact tag name, case-insensitive substring search on recipe name
- **Pagination** — configurable `page` and `size` parameters on list endpoints
- **Auto-generated docs** — interactive OpenAPI explorer at `/docs`

## Quick Start

> [!NOTE]
> Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
# Install dependencies
uv sync

# Apply database migrations
uv run alembic upgrade head

# Start the dev server
make dev
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to explore the API.

### Try it out

```bash
# Health check
curl http://localhost:8000/health

# Create a recipe
curl -s -X POST http://localhost:8000/recipes -H 'Content-Type: application/json' -d '{
  "name": "Pasta",
  "servings": 2,
  "prep_minutes": 5,
  "cook_minutes": 10,
  "ingredients": [{"name": "pasta", "quantity": 200, "unit": "g"}],
  "instruction_steps": [{"number": 1, "text": "Boil water"}],
  "tags": ["italian", "quick"]
}'

# List recipes filtered by tag
curl "http://localhost:8000/recipes?tag=italian"
```

## API Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/` | Root welcome | 200 |
| GET | `/health` | Health check | 200 |
| **Recipes** | | | |
| GET | `/recipes` | List recipes with pagination, tag filter, search | 200 |
| POST | `/recipes` | Create recipe with ingredients, steps, tags | 201, 409, 422 |
| GET | `/recipes/{id}` | Get full recipe detail | 200, 404 |
| PATCH | `/recipes/{id}` | Partial update (only provided fields change) | 200, 404 |
| DELETE | `/recipes/{id}` | Delete recipe (ingredients cascade) | 204, 404 |
| **Tags** | | | |
| GET | `/tags` | List tags with recipe counts (including zero-recipe tags) | 200 |
| POST | `/tags` | Create tag | 201, 409, 422 |
| GET | `/tags/{id}` | Get tag detail | 200, 404 |
| PATCH | `/tags/{id}` | Update tag name | 200, 404, 409 |
| DELETE | `/tags/{id}` | Delete tag | 204, 404 |

### Query Parameters

**GET /recipes**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (≥1) |
| `size` | int | 20 | Items per page (1–100) |
| `tag` | string | — | Filter by exact tag name |
| `search` | string | — | Case-insensitive substring match on recipe name |

**GET /tags**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (≥1) |
| `size` | int | 20 | Items per page (1–100) |
| `order` | string | `asc` | Sort order: `asc` or `desc` |

## Configuration

Environment variables are prefixed with `RECIPES_` and can be set via `.env` file or shell:

| Variable | Default | Description |
|----------|---------|-------------|
| `RECIPES_DATABASE_URL` | `sqlite+pysqlite:///./recipes.db` | Database connection string |
| `RECIPES_DEBUG` | `false` | Enable debug mode |

> [!TIP]
> Copy `.env.example` to `.env` to get started: `cp .env.example .env`

## Testing

```bash
# Run all tests
make test

# Run with verbose output
uv run pytest -vv

# Run specific test file
uv run pytest tests/test_recipes.py -q
```

Tests use an in-memory SQLite database per test for full isolation.

## Project Structure

```
├── src/
│   ├── main.py            # FastAPI app assembly
│   ├── config.py          # pydantic-settings configuration
│   ├── db.py              # Engine, session factory, dependencies
│   ├── models.py          # SQLModel ORM models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── enums.py           # Difficulty enum
│   └── routers/
│       ├── recipes.py     # Recipe CRUD endpoints
│       └── tags.py        # Tag endpoints
├── tests/
│   ├── conftest.py        # Test fixtures (in-memory DB, dependency override)
│   ├── test_recipes.py    # Recipe endpoint tests
│   └── test_tags.py       # Tag endpoint tests
├── alembic/               # Database migrations
├── docs/
│   ├── adr/               # Architecture Decision Records
│   ├── glossary.md        # Domain vocabulary
│   └── UAT.md             # User acceptance tests
├── Makefile               # dev, test commands
├── pyproject.toml         # Dependencies and project config
└── alembic.ini            # Alembic configuration
```
