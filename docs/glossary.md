# Glossary

- **Recipe** — a collection with a name, servings, prep/cook minutes, difficulty,
  an ordered list of instruction steps, and a set of ingredients and tags.
- **Ingredient** — a child row of a recipe: `name`, `quantity` (Decimal), `unit`
  (free text), `position` for ordering. Cascade-deleted with its recipe.
- **Step** — one ordered instruction (`number`, `text`); stored as JSON on the
  recipe, validated by Pydantic.
- **Tag** — a free-text label (`name`, unique) linked to recipes via the
  `recipe_tags` association table (many-to-many).
- **Difficulty** — enum on a recipe: `easy`, `medium`, `hard`.
- **Association table** — `recipe_tags`, the join table holding
  `recipe_id` / `tag_id` pairs for the many-to-many relationship.
- **Cascade delete-orphan** — SQLAlchemy relationship option: deleting a recipe
  deletes its ingredients; removing an ingredient from the collection deletes the
  row.
- **Numeric(10,3)** — SQLAlchemy column type storing decimals with 10 total
  digits, 3 after the point; surfaced as Python `Decimal`.
