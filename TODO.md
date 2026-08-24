# Recipe Collection API — Build Challenge

No copy-paste. You write every line. Docs exist to test your judgement, not hand
you answers:

- `docs/adr/0001-*.md` — the *decisions*. Read before each step, then implement.
- `docs/glossary.md` — vocabulary. Use it precisely.

Rules:

1. One step at a time. Finish + verify before the next.
2. Reading the ADR is allowed. Copying from it is not (it has no code anyway).
3. When stuck 15 min: re-read the ADR, then the SQLAlchemy/Pydantic docs, then ask.
4. Each step ends with a **Check** that must pass.

Stack: FastAPI · Pydantic v2 · SQLAlchemy 2.0 (sync) · Alembic · SQLite. pip + venv.

```bash
source .venv/bin/activate
```

---

## Step 0 — Orientation

- [x] Files scaffolded (all empty):

```
src/recipes_api/
  __init__.py      routers/{__init__,recipes,tags}.py
  config.py        schemas.py
  db.py            main.py
  models.py
tests/test_recipes.py
alembic/   docs/adr/   docs/glossary.md   requirements*.txt
```

Your job: fill every file below. Read ADR-0001 first — it exists because it matters.

---

## Step 1 — `config.py`

- [x] **Goal**: one settings object, parsed once, env-overridable.

Spec:
- `database_url` default `sqlite:///./recipes.db`
- `echo_sql` default off
- env prefix `RECIPES_` (so `RECIPES_DATABASE_URL` overrides)
- cheap to call repeatedly (memoized)

Traps to think about: where do env defaults belong in `pydantic-settings`? Is
`Settings()` expensive? Do you want it cached?

Check:

```bash
python -c "from src.config import Settings; print(Settings().database_url); print(Settings().debug)"
```

---

## Step 2 — `db.py`

- [x] **Goal**: engine, session factory, declarative base, per-request session.

Spec:
- engine built from config; SQLite needs a connection arg FastAPI threadpool
  would otherwise trip over — discover which.
- session factory: sessions must not autoflush, and must stay usable *after*
  commit (imagine building a response from objects you just wrote).
- `Base` — your models inherit it.
- `get_db` — yields one session per request, guaranteed closed. FastAPI calls it
  a *dependency*; the yield variant is special. Why?

Check:

```bash
python -c "from src.db import engine, SessionLocal; print(engine.url)"
```

---

## Step 3 — `models.py`

- [x] **Goal**: `recipes`, `ingredients`, `tags`, `recipe_tags`. Per ADR-0001.

Spec:
- `Recipe`: name **unique** + indexed; description; servings; prep/cook minutes;
  difficulty; instructions as JSON; created/updated timestamps (updated = changes
  on update).
- `Ingredient`: child of recipe, `ON DELETE CASCADE`; ordered by a `position`
  column; quantity must survive `0.5` cleanly (Decimal); unit free text.
- `Tag`: name unique + indexed.
- M2M: `recipe_tags` — a plain `Table`, not a model. Cascade both sides.
- Difficulty: a `str`-subclassed enum, stored as string.

Traps to think about:
- SQLite has no `NOW()`. What does `func.now()` actually render to?
- Two timestamps: one only set at insert, one refreshed on every update. Which
  SQLAlchemy keyword does each?
- Deleting a recipe must delete its ingredients — at the ORM level, not just DB.
  You're writing the relationship option, not the migration.

Check:

```bash
python -c "from recipes_api.models import Recipe, Ingredient, Tag; print('models ok')"
```

---

## Step 4 — Alembic

- [x] **Goal**: version-controlled schema. First migration via autogenerate.

Spec:
- `alembic init alembic`
- wire `env.py` to your `Base.metadata` so autogenerate sees your models.
- same SQLite file as config (`sqlite:///./recipes.db`).
- generate initial migration, then apply it.

Traps: importing the package so models register on `Base` (a noqa'd import is
common for a reason); env.py imports your settings from inside a function, not
at module top — why would that be?

Check — all 5 tables exist (4 yours + `alembic_version`):

```bash
python -c "import sqlite3; print(sqlite3.connect('recipes.db').execute(\"select name from sqlite_master where type='table'\").fetchall())"
```

---

## Step 5 — `schemas.py`

- [x] **Goal**: request/response contracts. Two worlds: ORM models (DB) and Pydantic
models (API). Don't confuse them.

Spec:
- `IngredientIn` (name, quantity>0, unit) and `IngredientOut` (+id, position)
- `StepIn` (number>0, text)
- `RecipeCreate` — nested ingredients + steps + tag *names* (strings). Everything
  validated: servings>0, minutes>=0, non-empty names.
- `RecipeUpdate` — same fields, all optional. Partial updates.
- `RecipeRead` — full, including tags as plain `list[str]`, ingredients as
  `IngredientOut`. Can be built from ORM objects.
- `RecipeListItem` — id, name, difficulty, servings, `total_min`, `tag_count`.
  These last two are *computed*; where do they come from?
- `TagCreate` / `TagRead` (with `recipe_count`).
- Both numeric types: quantity is `Decimal`, ids are `int`. Pydantic + Decimal:
  a known friction point. Keep `IngredientIn.quantity` Decimal too.

Traps: what does `from_attributes=True` buy you? Does `RecipeRead` deserialize
from a Recipe ORM object directly, or do you hand-build it? (ADR hints: the
tags→names mapping is a router job.)

Check:

```bash
python -c "from recipes_api.schemas import RecipeCreate; print(RecipeCreate(name='x', servings=2, prep_min=5, cook_min=10))"
```

Try feeding it bad input and watch it fail:

```bash
python -c "from recipes_api.schemas import RecipeCreate; RecipeCreate(name='', servings=0, prep_min=-1, cook_min=10)"  # expect ValidationError
```

---

## Step 6 — `routers/recipes.py`

- [x] **Goal**: the interesting route file. CRUD + list with page/size pagination,
tag filter, name search.

Spec:
- `POST /recipes` → 201. Resolve tag names: existing tags reused, unknown ones
  created. Ingredients get `position` = their index. Instructions persist.
- `GET /recipes?page=1&size=20&tag=...&search=...` → list. Tag filter exact,
  search is a case-insensitive substring on **name**. Return the `RecipeListItem`
  shape.
- `GET /recipes/{id}` → full detail. 404 if missing.
- `PATCH /recipes/{id}` → partial update. *Only* provided fields change. Full
  replacement semantics for `ingredients`/`tags`/`instructions`.
- `DELETE /recipes/{id}` → 204. Ingredients cascade.

Traps (the meat of this step — figure each out):
- Reading a recipe and its children: lazy loads cause **N+1 queries** on lists.
  What loader fixes that? (`selectinload` is the modern answer — justify it
  against `joinedload`.)
- `PATCH` + `model_dump(exclude_unset=True)`: why `exclude_unset` and not just
  `exclude_none`? What breaks if the client explicitly sends `null`?
- Replace-vs-merge: when you reassign `recipe.ingredients = [...]`, old child
  rows must vanish. Which relationship option makes SQLAlchemy handle that?
- Unique name → IntegrityError on insert. Do you catch it here, or let it bubble?
  (What would the client see? Check what FastAPI does with an unhandled
  `IntegrityError` — 500, not 409. Decide how to handle duplicates.)
- SQLite + `ilike` — case-insensitive? Verify, don't assume.

Check:

```bash
python -c "from recipes_api.routers.recipes import router; print(len(router.routes), 'routes')"
```

---

## Step 7 — `routers/tags.py`

**Goal**: tags with real aggregation.

Spec:
- `GET /tags` → name + `recipe_count`. **Including tags with zero recipes.**
- `POST /tags` → 201; duplicate name → **409**, not 500.

Traps:
- Zero-recipe tags vanish under an inner join. What kind of join + group_by
  keeps them? Where does the count come from — `func.count(Tag.recipes)` or a
  column? Try both, read the SQL.
- Duplicate: the *DB* enforces uniqueness. Catch `IntegrityError`, `rollback()`
  the session (why mandatory?), map to 409.

Check:

```bash
python -c "from recipes_api.routers.tags import router; print(len(router.routes), 'routes')"
```

---

## Step 8 — `main.py`

**Goal**: app assembly.

Spec:
- FastAPI app, sensible title/version/description.
- Mount both routers.
- `GET /health` → `{"status": "ok"}`.

Check:

```bash
uvicorn recipes_api.main:app --reload   # then hit http://127.0.0.1:8000/docs
curl -s localhost:8000/health
curl -s -X POST localhost:8000/recipes -H 'content-type: application/json' \
  -d '{"name":"Pasta","servings":2,"prep_min":5,"cook_min":10,"ingredients":[{"name":"pasta","quantity":200,"unit":"g"}],"tags":["italian","quick"]}'
curl -s "localhost:8000/recipes?tag=italian"
```

---

## Step 9 — `tests/test_recipes.py`

**Goal**: isolation, no real DB pollution. pytest + `TestClient`.

Spec — the fixture:
- in-memory SQLite engine per test
- `Base.metadata.create_all` on it
- override the `get_db` dependency so routes hit the test DB
- cleanup between tests

Then cover, at minimum:
1. create → 201, ingredients+tags echoed
2. missing recipe → 404
3. pagination: 3 items, `size=2` page 1 → 2, page 2 → 1
4. tag filter isolates results
5. search is case-insensitive substring
6. PATCH changes only provided field
7. DELETE cascades (verify ingredient rows actually gone)
8. duplicate tag → 409
9. invalid payloads → 422 (servings=0, empty name, negative minutes)
10. tag counts: tag on 2 recipes → `recipe_count: 2`; orphan tag → still listed with 0

Trap: dependency override is per-app global state — why must it be cleared after
each test? What happens to tests running after a dirty override?

Check:

```bash
pytest -q
```

---

## Step 10 — `README.md`

Spec:
- quickstart: activate venv, migrate, run, open `/docs`
- test command
- endpoint table (method / path / notes)

This one is documentation; write it like a human would consume it.

---

## Step 11 — Final verification

- [x] fresh DB + `alembic upgrade head` → clean
- [x] `uvicorn recipes_api.main:app --reload` → `/docs` renders, every endpoint 200/4xx as designed
- [ ] `pytest -q` all green
- [ ] README quickstart reproduces from scratch

---

## Stretch (day-leftover)

- [ ] `GET /recipes/stats` — total, avg prep+cook, top 5 tags (aggregations, no ORM loop)
- [ ] description search too, or real FTS5
- [ ] rating: `POST /recipes/{id}/rate` + average in `RecipeRead`
- [ ] soft delete: `deleted_at`, `?include_deleted`
- [ ] seed script: 10 believable recipes with tags
- [ ] `GET /recipes/{id}/ingredients` with totals computed on the fly
