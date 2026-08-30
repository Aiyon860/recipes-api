import httpx2 as httpx
import pytest
from sqlmodel import Session, func, select

from src.models import Ingredient


class TestRecipes:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client

    def test_create_recipe(self):
        """POST /v1/recipes → 201, response includes ingredients + tags"""
        payload = {
            "name": "Boiled Egg",
            "ingredients": [{"name": "egg", "quantity": 1, "unit": "pcs"}],
            "instruction_steps": [
                {"number": 1, "text": "Boil water, add egg, wait 8 min"}
            ],
            "tags": ["breakfast"],
        }
        res = self.client.post("/v1/recipes", json=payload)
        assert res.status_code == httpx.codes.CREATED

        data = res.json()["data"]
        targets = ["name", "ingredients", "tags"]
        for target in targets:
            assert target in data

        assert data["name"] == "Boiled Egg"
        assert len(data["ingredients"]) == 1
        assert data["tags"] == ["breakfast"]

    def test_get_recipe_not_found(self):
        """GET /v1/recipes/999 → 404"""
        res = self.client.get("/v1/recipes/999")
        assert res.status_code == httpx.codes.NOT_FOUND

        res_dict = res.json()
        assert "detail" in res_dict
        assert res_dict["detail"] == "Recipe with id=999 is not found."

    def test_list_recipes_pagination(self):
        """GET /v1/recipes?page=1&size=2 → 2 items, page=2 → 1 item"""
        payloads = [
            {
                "name": "Spaghetti Carbonara",
                "description": "Italian pasta dish with eggs and cheese",
                "servings": 2,
                "prep_minutes": 10,
                "cook_minutes": 20,
                "difficulty": "medium",
                "ingredients": [
                    {"name": "spaghetti", "quantity": 200, "unit": "g"},
                    {"name": "eggs", "quantity": 2, "unit": "pcs"},
                    {"name": "parmesan", "quantity": 50, "unit": "g"},
                ],
                "instruction_steps": [
                    {"number": 1, "text": "Boil pasta"},
                    {"number": 2, "text": "Mix eggs and cheese"},
                    {"number": 3, "text": "Combine pasta with sauce"},
                ],
                "tags": ["italian", "pasta"],
            },
            {
                "name": "Boiled Egg",
                "ingredients": [{"name": "egg", "quantity": 1, "unit": "pcs"}],
                "instruction_steps": [
                    {"number": 1, "text": "Boil water, add egg, wait 8 min"}
                ],
                "tags": ["breakfast"],
            },
            {
                "name": "Pasta Aglio e Olio",
                "description": "Simple garlic pasta",
                "servings": 1,
                "ingredients": [
                    {"name": "spaghetti", "quantity": 150, "unit": "gram"},
                    {"name": "garlic", "quantity": 4, "unit": "pcs"},
                ],
                "instruction_steps": [
                    {"number": 1, "text": "Boil pasta"},
                    {"number": 2, "text": "Sauté garlic in olive oil"},
                    {"number": 3, "text": "Toss pasta in oil"},
                ],
                "tags": ["italian", "pasta"],
            },
        ]
        for payload in payloads:
            res = self.client.post("/v1/recipes", json=payload)
            assert res.status_code == httpx.codes.CREATED

        params_array = [{"page": 1, "size": 2}, {"page": 2, "size": 2}]
        for params in params_array:
            res = self.client.get("/v1/recipes", params=params)
            assert res.status_code == httpx.codes.OK

            res_dict = res.json()
            total = res_dict["total"]
            page = res_dict["page"]
            size = res_dict["size"]
            expected = min(size, total - (page - 1) * size)
            assert len(res_dict["data"]) == expected

    def test_list_recipes_filter_by_tag(self):
        """GET /v1/recipes?tag=italian → only italian recipes"""
        payloads = [
            {
                "name": "Spaghetti Carbonara",
                "description": "Italian pasta dish with eggs and cheese",
                "servings": 2,
                "prep_minutes": 10,
                "cook_minutes": 20,
                "difficulty": "medium",
                "ingredients": [
                    {"name": "spaghetti", "quantity": 200, "unit": "g"},
                    {"name": "eggs", "quantity": 2, "unit": "pcs"},
                    {"name": "parmesan", "quantity": 50, "unit": "g"},
                ],
                "instruction_steps": [
                    {"number": 1, "text": "Boil pasta"},
                    {"number": 2, "text": "Mix eggs and cheese"},
                    {"number": 3, "text": "Combine pasta with sauce"},
                ],
                "tags": ["italian", "pasta"],
            },
            {
                "name": "Boiled Egg",
                "ingredients": [{"name": "egg", "quantity": 1, "unit": "pcs"}],
                "instruction_steps": [
                    {"number": 1, "text": "Boil water, add egg, wait 8 min"}
                ],
                "tags": ["breakfast"],
            },
        ]
        for payload in payloads:
            res = self.client.post("/v1/recipes", json=payload)
            assert res.status_code == httpx.codes.CREATED

        param = {"tag": "italian"}
        res = self.client.get("/v1/recipes", params=param)
        assert res.status_code == httpx.codes.OK

        data = res.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Spaghetti Carbonara"

    def test_list_recipes_search_by_name(self):
        """GET /v1/recipes?search=pasta → case-insensitive substring match"""
        payloads = [
            {
                "name": "Spaghetti Carbonara",
                "description": "Italian pasta dish with eggs and cheese",
                "servings": 2,
                "prep_minutes": 10,
                "cook_minutes": 20,
                "difficulty": "medium",
                "ingredients": [
                    {"name": "spaghetti", "quantity": 200, "unit": "g"},
                    {"name": "eggs", "quantity": 2, "unit": "pcs"},
                    {"name": "parmesan", "quantity": 50, "unit": "g"},
                ],
                "instruction_steps": [
                    {"number": 1, "text": "Boil pasta"},
                    {"number": 2, "text": "Mix eggs and cheese"},
                    {"number": 3, "text": "Combine pasta with sauce"},
                ],
                "tags": ["italian", "pasta"],
            },
            {
                "name": "Boiled Egg",
                "ingredients": [{"name": "egg", "quantity": 1, "unit": "pcs"}],
                "instruction_steps": [
                    {"number": 1, "text": "Boil water, add egg, wait 8 min"}
                ],
                "tags": ["breakfast"],
            },
            {
                "name": "Pasta Aglio e Olio",
                "description": "Simple garlic pasta",
                "servings": 1,
                "ingredients": [
                    {"name": "spaghetti", "quantity": 150, "unit": "gram"},
                    {"name": "garlic", "quantity": 4, "unit": "pcs"},
                ],
                "instruction_steps": [
                    {"number": 1, "text": "Boil pasta"},
                    {"number": 2, "text": "Sauté garlic in olive oil"},
                    {"number": 3, "text": "Toss pasta in oil"},
                ],
                "tags": ["italian", "pasta"],
            },
        ]
        for payload in payloads:
            res = self.client.post("/v1/recipes", json=payload)
            assert res.status_code == httpx.codes.CREATED

        param = {"search": "pasta"}
        res = self.client.get("/v1/recipes", params=param)
        assert res.status_code == httpx.codes.OK

        data = res.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Pasta Aglio e Olio"

    def test_update_recipe_partial(self):
        """PATCH /v1/recipes/{id} → only provided fields change"""
        original = {
            "name": "Boiled Egg",
            "description": "Simple boiled egg",
            "servings": 2,
            "prep_minutes": 5,
            "cook_minutes": 10,
            "difficulty": "easy",
            "ingredients": [
                {"name": "egg", "quantity": 2, "unit": "pcs"},
                {"name": "water", "quantity": 500, "unit": "ml"},
            ],
            "instruction_steps": [
                {"number": 1, "text": "Boil water, add egg, wait 8 min"}
            ],
            "tags": ["breakfast"],
        }
        res = self.client.post("/v1/recipes", json=original)
        assert res.status_code == httpx.codes.CREATED

        data = res.json()["data"]
        recipe_id = data["id"]
        original_ingredients = data["ingredients"]  # Decimal serialized by Pydantic
        update_payload = {"name": "Boiled Egg (Updated)", "servings": 4}
        res = self.client.patch(f"/v1/recipes/{recipe_id}", json=update_payload)
        assert res.status_code == httpx.codes.OK

        data = res.json()["data"]
        # Changed
        assert data["name"] == update_payload["name"]
        assert data["servings"] == update_payload["servings"]

        # Not Changed
        assert data["description"] == original["description"]
        assert data["ingredients"] == original_ingredients
        assert data["tags"] == original["tags"]

    def test_delete_recipe_cascades_ingredients(self, db_engine):
        """DELETE /v1/recipes/{id} → ingredients row deleted"""
        payload = {
            "name": "Boiled Egg",
            "description": "Simple boiled egg",
            "servings": 2,
            "prep_minutes": 5,
            "cook_minutes": 10,
            "difficulty": "easy",
            "ingredients": [
                {"name": "egg", "quantity": 2, "unit": "pcs"},
                {"name": "water", "quantity": 500, "unit": "ml"},
            ],
            "instruction_steps": [
                {"number": 1, "text": "Boil water, add egg, wait 8 min"}
            ],
            "tags": ["breakfast"],
        }
        res = self.client.post("/v1/recipes", json=payload)
        assert res.status_code == httpx.codes.CREATED

        recipe_id = res.json()["data"]["id"]
        res = self.client.delete(f"/v1/recipes/{recipe_id}")
        assert res.status_code == httpx.codes.NO_CONTENT

        res = self.client.get(f"/v1/recipes/{recipe_id}")
        assert res.status_code == httpx.codes.NOT_FOUND

        # Check ingredients table directly as we don't have ingredient endpoints
        with Session(db_engine) as session:
            count = session.exec(
                select(func.count(Ingredient.id)).where(
                    Ingredient.recipe_id == recipe_id
                )
            ).one()
            assert count == 0

    def test_create_recipe_validation_error(self):
        """POST /v1/recipes with bad data → 422"""
        payload = {
            "name": "Bad Recipe",
            "ingredients": [{"name": "x", "quantity": -1, "unit": "g"}],
            "instruction_steps": [{"number": 1, "text": "Do it"}],
            "tags": ["test"],
        }
        res = self.client.post("/v1/recipes", json=payload)
        assert res.status_code == httpx.codes.UNPROCESSABLE_CONTENT
