# Plan: Implement API Versioning (URL-based)

## Context
Implement URL-based API versioning dengan prefix `/v1/`.
Hanya ada v1 routes, tidak ada unversioned.

## Current Structure
```
src/
  routers/
    __init__.py
    recipes.py
    tags.py
  main.py
tests/
  conftest.py
  test_recipes.py
  test_tags.py
```

## Target Structure
```
src/
  routers/
    __init__.py
    v1/
      __init__.py
      recipes.py
      tags.py
  main.py
tests/
  conftest.py
  test_recipes.py  (updated URLs)
  test_tags.py     (updated URLs)
```

---

## Implementation Steps

### 1. Create v1 directory
```bash
mkdir -p src/routers/v1
touch src/routers/v1/__init__.py
```

### 2. Move & update recipes.py
- Pindahkan `src/routers/recipes.py` → `src/routers/v1/recipes.py`
- Update prefix: `APIRouter(prefix="/recipes", tags=["v1", "Recipes"])`
- Imports tetap sama (schemas shared)

### 3. Move & update tags.py
- Pindahkan `src/routers/tags.py` → `src/routers/v1/tags.py`
- Update prefix: `APIRouter(prefix="/tags", tags=["v1", "Tags"])`

### 4. Update main.py
```python
from src.routers.v1.recipes import router as recipes_router
from src.routers.v1.tags import router as tags_router

app = FastAPI()

@app.get("/")
def root():
    return {"hello": "world"}

@app.get("/health")
def check_health():
    return {"status": "ok"}

app.include_router(recipes_router, prefix="/v1")
app.include_router(tags_router, prefix="/v1")
```

### 5. Clean up
- Hapus `src/routers/recipes.py`
- Hapus `src/routers/tags.py`

### 6. Update tests
Update semua URL di test files:

**test_recipes.py:**
| Old | New |
|-----|-----|
| `POST /recipes` | `POST /v1/recipes` |
| `GET /recipes` | `GET /v1/recipes` |
| `GET /recipes/{id}` | `GET /v1/recipes/{id}` |
| `PATCH /recipes/{id}` | `PATCH /v1/recipes/{id}` |
| `DELETE /recipes/{id}` | `DELETE /v1/recipes/{id}` |

**test_tags.py:**
| Old | New |
|-----|-----|
| `POST /tags` | `POST /v1/tags` |
| `GET /tags` | `GET /v1/tags` |
| `GET /tags/{id}` | `GET /v1/tags/{id}` |
| `PATCH /tags/{id}` | `PATCH /v1/tags/{id}` |
| `DELETE /tags/{id}` | `DELETE /v1/tags/{id}` |

---

## Resulting Endpoints

| Method | Path |
|--------|------|
| GET | `/` |
| GET | `/health` |
| GET | `/v1/recipes` |
| POST | `/v1/recipes` |
| GET | `/v1/recipes/{id}` |
| PATCH | `/v1/recipes/{id}` |
| DELETE | `/v1/recipes/{id}` |
| GET | `/v1/tags` |
| POST | `/v1/tags` |
| GET | `/v1/tags/{id}` |
| PATCH | `/v1/tags/{id}` |
| DELETE | `/v1/tags/{id}` |

---

## Notes
- **Schemas shared** - tidak duplikasi Pydantic models
- **Route lama dihapus** - `/recipes` tidak ada lagi
- **Breaking change** - clients harus update ke `/v1/`
- **Future** - v2 tinggal tambah `v2/` folder
- **Tests flat** - hanya update URLs, tidak restructure

## Verification
```bash
# Test v1
curl localhost:8000/v1/recipes

# Pastikan route lama hilang
curl localhost:8000/recipes  # harus 404

# Run tests
pytest -q
```
