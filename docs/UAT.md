# UAT — Recipe Collection API

**Base URL**: `http://127.0.0.1:8000`

> Ambil `id` dari setiap Create (C01/C02) sebagai `{id}` untuk test berikutnya.
> Run: `uvicorn src.main:app --reload` sebelum mulai.

---

## POST /recipes — Create

### C01: Valid recipe (full)

```bash
curl -s -X POST http://127.0.0.1:8000/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spaghetti Carbonara",
    "description": "Italian pasta dish with eggs and cheese",
    "servings": 2,
    "prep_minutes": 10,
    "cook_minutes": 20,
    "difficulty": "medium",
    "ingredients": [
      {"name": "spaghetti", "quantity": 200, "unit": "g"},
      {"name": "eggs", "quantity": 2, "unit": "pcs"},
      {"name": "parmesan", "quantity": 50, "unit": "g"}
    ],
    "instruction_steps": [
      {"number": 1, "text": "Boil pasta"},
      {"number": 2, "text": "Mix eggs and cheese"},
      {"number": 3, "text": "Combine pasta with sauce"}
    ],
    "tags": ["italian", "pasta"]
  }'
```

**Expected**: `201 Created`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Spaghetti Carbonara",
    "description": "Italian pasta dish with eggs and cheese",
    "servings": 2,
    "prep_minutes": 10,
    "cook_minutes": 20,
    "difficulty": "medium",
    "instruction_steps": [
      {"number": 1, "text": "Boil pasta"},
      {"number": 2, "text": "Mix eggs and cheese"},
      {"number": 3, "text": "Combine pasta with sauce"}
    ],
    "tags": ["italian", "pasta"],
    "ingredients": [
      {"id": 1, "name": "spaghetti", "quantity": 200, "unit": "g", "position": 0},
      {"id": 2, "name": "eggs", "quantity": 2, "unit": "pcs", "position": 1},
      {"id": 3, "name": "parmesan", "quantity": 50, "unit": "g", "position": 2}
    ],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

**Verify**: `GET /recipes/1` → data sama.

---

### C02: Minimal recipe (defaults applied)

```bash
curl -s -X POST http://127.0.0.1:8000/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Boiled Egg",
    "ingredients": [
      {"name": "egg", "quantity": 1, "unit": "pcs"}
    ],
    "instruction_steps": [
      {"number": 1, "text": "Boil water, add egg, wait 8 min"}
    ],
    "tags": ["breakfast"]
  }'
```

**Expected**: `201 Created`

```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Boiled Egg",
    "description": null,
    "servings": 1,
    "prep_minutes": 0,
    "cook_minutes": 0,
    "difficulty": null,
    "tags": ["breakfast"],
    "ingredients": [
      {"id": 4, "name": "egg", "quantity": 1, "unit": "pcs", "position": 0}
    ]
  }
}
```

**Verify**: defaults `servings=1`, `prep_minutes=0`, `cook_minutes=0`, `difficulty=null`, `description=null`.

---

### C03: Duplicate name → 409

```bash
curl -s -X POST http://127.0.0.1:8000/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spaghetti Carbonara",
    "ingredients": [{"name": "pasta", "quantity": 100, "unit": "g"}],
    "instruction_steps": [{"number": 1, "text": "Cook"}],
    "tags": ["italian"]
  }'
```

**Expected**: `409 Conflict`

```json
{
  "detail": "Recipe with name 'Spaghetti Carbonara' already exists."
}
```

---

### C04: Invalid payload → 422

```bash
curl -s -X POST http://127.0.0.1:8000/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "",
    "servings": 0,
    "ingredients": [],
    "instruction_steps": [],
    "tags": []
  }'
```

**Expected**: `422 Unprocessable Entity`

```json
{
  "detail": [
    {"loc": ["body", "name"], "msg": "String should have at least 1 character", "type": "string_too_short"},
    {"loc": ["body", "servings"], "msg": "Input should be greater than 0", "type": "value_error"}
  ]
}
```

---

### C05: Invalid ingredient quantity → 422

```bash
curl -s -X POST http://127.0.0.1:8000/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bad Recipe",
    "ingredients": [{"name": "x", "quantity": -1, "unit": "g"}],
    "instruction_steps": [{"number": 1, "text": "Do it"}],
    "tags": ["test"]
  }'
```

**Expected**: `422 Unprocessable Entity`

```json
{
  "detail": [
    {"loc": ["body", "ingredients", 0, "quantity"], "msg": "Input should be greater than 0", "type": "value_error"}
  ]
}
```

---

## GET /recipes — List

### L01: Default (no params)

```bash
curl -s "http://127.0.0.1:8000/recipes"
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "page": 1,
  "size": 20,
  "total": 2,
  "pages": 1,
  "tag": null,
  "search": null,
  "data": [
    {
      "id": 1,
      "name": "Spaghetti Carbonara",
      "difficulty": "medium",
      "servings": 2,
      "total_min": 30,
      "tag_count": 2
    },
    {
      "id": 2,
      "name": "Boiled Egg",
      "difficulty": null,
      "servings": 1,
      "total_min": 0,
      "tag_count": 1
    }
  ]
}
```

**Verify**: `total` = jumlah semua resep, `pages` = ceil(total/size).

---

### L02: Pagination

```bash
curl -s "http://127.0.0.1:8000/recipes?page=1&size=1"
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "page": 1,
  "size": 1,
  "total": 2,
  "pages": 2,
  "data": [
    {
      "id": 1,
      "name": "Spaghetti Carbonara"
    }
  ]
}
```

**Verify**: hanya 1 item, `pages=2`.

---

### L03: Filter by tag

```bash
curl -s "http://127.0.0.1:8000/recipes?tag=italian"
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "page": 1,
  "size": 20,
  "total": 1,
  "pages": 1,
  "tag": "italian",
  "data": [
    {
      "id": 1,
      "name": "Spaghetti Carbonara"
    }
  ]
}
```

**Verify**: hanya resep dengan tag "italian", `total=1`.

---

### L04: Search by name (case-insensitive)

```bash
curl -s "http://127.0.0.1:8000/recipes?search=spaghetti"
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "page": 1,
  "size": 20,
  "total": 1,
  "search": "spaghetti",
  "data": [
    {
      "id": 1,
      "name": "Spaghetti Carbonara"
    }
  ]
}
```

**Verify**: case-insensitive, "spaghetti" match "Spaghetti Carbonara".

---

### L05: Combined tag + search

```bash
curl -s "http://127.0.0.1:8000/recipes?tag=italian&search=carbonara"
```

**Expected**: `200 OK`, `total=1`, hanya "Spaghetti Carbonara".

---

### L06: No match

```bash
curl -s "http://127.0.0.1:8000/recipes?search=sushimaster"
```

**Expected**: `200 OK`, `total=0`, `pages=0`, `data=[]`.

---

## GET /recipes/{id} — Detail

### D01: Valid id

```bash
curl -s "http://127.0.0.1:8000/recipes/1"
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Spaghetti Carbonara",
    "description": "Italian pasta dish with eggs and cheese",
    "servings": 2,
    "prep_minutes": 10,
    "cook_minutes": 20,
    "difficulty": "medium",
    "instruction_steps": [
      {"number": 1, "text": "Boil pasta"},
      {"number": 2, "text": "Mix eggs and cheese"},
      {"number": 3, "text": "Combine pasta with sauce"}
    ],
    "tags": ["italian", "pasta"],
    "ingredients": [
      {"id": 1, "name": "spaghetti", "quantity": 200, "unit": "g", "position": 0},
      {"id": 2, "name": "eggs", "quantity": 2, "unit": "pcs", "position": 1},
      {"id": 3, "name": "parmesan", "quantity": 50, "unit": "g", "position": 2}
    ],
    "created_at": "...",
    "updated_at": "..."
  }
}
```

**Verify**: ada `instruction_steps`, `tags` (list string), `ingredients` (list dengan `id`, `position`).

---

### D02: Non-existent id → 404

```bash
curl -s "http://127.0.0.1:8000/recipes/99999"
```

**Expected**: `404 Not Found`

```json
{
  "detail": "Recipe with id=99999 is not found."
}
```

---

## PATCH /recipes/{id} — Update

> Semua test di bawah pakai PATCH. Bisa juga PUT, hasil sama.

### U01: Update name only

```bash
curl -s -X PATCH http://127.0.0.1:8000/recipes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spaghetti Carbonara Classic"
  }'
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Spaghetti Carbonara Classic",
    "description": "Italian pasta dish with eggs and cheese",
    "servings": 2,
    "prep_minutes": 10,
    "cook_minutes": 20,
    "tags": ["italian", "pasta"],
    "ingredients": [
      {"id": 1, "name": "spaghetti", "quantity": 200, "unit": "g", "position": 0},
      {"id": 2, "name": "eggs", "quantity": 2, "unit": "pcs", "position": 1},
      {"id": 3, "name": "parmesan", "quantity": 50, "unit": "g", "position": 2}
    ]
  }
}
```

**Verify**: hanya `name` berubah, `ingredients`/`tags`/`description` tetap.

---

### U02: Clear description (null)

```bash
curl -s -X PATCH http://127.0.0.1:8000/recipes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "description": null
  }'
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "description": null,
    "name": "Spaghetti Carbonara Classic"
  }
}
```

**Verify**: `description` jadi `null` (bukan tetap lama). Ini bukti `exclude_unset=True` bekerja.

---

### U03: Replace ingredients

```bash
curl -s -X PATCH http://127.0.0.1:8000/recipes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": [
      {"name": "spaghetti", "quantity": 250, "unit": "g"},
      {"name": "eggs", "quantity": 3, "unit": "pcs"},
      {"name": "guanciale", "quantity": 100, "unit": "g"},
      {"name": "black pepper", "quantity": 5, "unit": "g"}
    ]
  }'
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "ingredients": [
      {"id": 7, "name": "spaghetti", "quantity": 250, "unit": "g", "position": 0},
      {"id": 8, "name": "eggs", "quantity": 3, "unit": "pcs", "position": 1},
      {"id": 9, "name": "guanciale", "quantity": 100, "unit": "g", "position": 2},
      {"id": 10, "name": "black pepper", "quantity": 5, "unit": "g", "position": 3}
    ]
  }
}
```

**Verify**: ingredient lama (parmesan) **hilang**, 4 ingredient baru ada. `position` mulai dari 0.

---

### U04: Replace tags

```bash
curl -s -X PATCH http://127.0.0.1:8000/recipes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["italian", "classic", "dinner"]
  }'
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "tags": ["italian", "classic", "dinner"]
  }
}
```

**Verify**: tag "pasta" **hilang**, "classic" dan "dinner" **baru**. Tag "italian" tetap (reuse).

---

### U05: Clear tags (empty array)

```bash
curl -s -X PATCH http://127.0.0.1:8000/recipes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "tags": []
  }'
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "tags": []
  }
}
```

**Verify**: semua tag resep ini **hilang**. Tag di tabel `t_tags` tetap ada (tidak cascade).

---

### U06: Replace instruction_steps

```bash
curl -s -X PATCH http://127.0.0.1:8000/recipes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "instruction_steps": [
      {"number": 1, "text": "Cook spaghetti al dente"},
      {"number": 2, "text": "Crisp guanciale in pan"},
      {"number": 3, "text": "Mix eggs, cheese, pepper"},
      {"number": 4, "text": "Toss hot pasta with egg mixture and guanciale"}
    ]
  }'
```

**Expected**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": 1,
    "instruction_steps": [
      {"number": 1, "text": "Cook spaghetti al dente"},
      {"number": 2, "text": "Crisp guanciale in pan"},
      {"number": 3, "text": "Mix eggs, cheese, pepper"},
      {"number": 4, "text": "Toss hot pasta with egg mixture and guanciale"}
    ]
  }
}
```

**Verify**: steps lama (3 langkah) **hilang**, steps baru (4 langkah) ada.

---

### U07: Non-existent id → 404

```bash
curl -s -X PATCH http://127.0.0.1:8000/recipes/99999 \
  -H "Content-Type: application/json" \
  -d '{"name": "Nope"}'
```

**Expected**: `404 Not Found`

```json
{
  "detail": "Recipe with id=99999 is not found."
}
```

---

## DELETE /recipes/{id}

### X01: Valid delete

```bash
curl -s -X DELETE http://127.0.0.1:8000/recipes/2
```

**Expected**: `204 No Content` (empty body)

**Verify**:
1. `GET /recipes/2` → `404`
2. `GET /recipes?search=boiled` → `total=0`
3. Check DB: `SELECT * FROM t_ingredients WHERE recipe_id=2` → 0 rows
4. Check DB: `SELECT * FROM t_recipe_tags WHERE recipe_id=2` → 0 rows

---

### X02: Non-existent id → 404

```bash
curl -s -X DELETE http://127.0.0.1:8000/recipes/99999
```

**Expected**: `404 Not Found`

```json
{
  "detail": "Recipe with id=99999 is not found."
}
```

---

## Ringkasan Checkpoint

| # | Endpoint | Status | Verifikasi |
|---|---|---|---|
| C01 | POST /recipes | 201 | id=1, name, tags, ingredients, instruction_steps |
| C02 | POST /recipes | 201 | defaults: servings=1, minutes=0, difficulty=null |
| C03 | POST /recipes | 409 | duplicate name |
| C04 | POST /recipes | 422 | name="", servings=0 |
| C05 | POST /recipes | 422 | quantity=-1 |
| L01 | GET /recipes | 200 | total=2 (setelah C01+C02) |
| L02 | GET /recipes?page=1&size=1 | 200 | 1 item, pages=2 |
| L03 | GET /recipes?tag=italian | 200 | hanya C01 |
| L04 | GET /recipes?search=spaghetti | 200 | hanya C01 |
| L05 | GET /recipes?tag=italian&search=carbonara | 200 | 1 match |
| L06 | GET /recipes?search=sushimaster | 200 | 0 items |
| D01 | GET /recipes/1 | 200 | full detail + steps + tags + ingredients |
| D02 | GET /recipes/99999 | 404 | not found |
| U01 | PATCH /recipes/1 | 200 | name berubah, lainnya tetap |
| U02 | PATCH /recipes/1 | 200 | description=null |
| U03 | PATCH /recipes/1 | 200 | ingredients lama hilang, baru ada |
| U04 | PATCH /recipes/1 | 200 | tags berubah |
| U05 | PATCH /recipes/1 | 200 | tags=[] |
| U06 | PATCH /recipes/1 | 200 | instruction_steps berubah |
| U07 | PATCH /recipes/99999 | 404 | not found |
| X01 | DELETE /recipes/2 | 204 | cascading verified |
| X02 | DELETE /recipes/99999 | 404 | not found |
