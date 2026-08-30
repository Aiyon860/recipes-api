import httpx2 as httpx
import pytest


class TestTags:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client

    def test_create_tag(self):
        """POST /v1/tags → 201, id + name returned"""
        payload = {"name": "Indonesian"}
        res = self.client.post("/v1/tags", json=payload)
        assert res.status_code == httpx.codes.CREATED

        data = res.json()["data"]
        assert data["name"] == payload["name"]

    def test_duplicate_tag_409(self):
        """POST /v1/tags with same name twice → 409"""
        payloads = [{"name": "Indonesia"}, {"name": "Indonesia"}]
        res = self.client.post("/v1/tags", json=payloads[0])
        assert res.status_code == httpx.codes.CREATED

        res = self.client.post("/v1/tags", json=payloads[1])
        assert res.status_code == httpx.codes.CONFLICT

    def test_list_tags(self):
        """GET /v1/tags → returns all tags sorted by name"""
        payloads = [{"name": "Lunch"}, {"name": "Breakfast"}, {"name": "Dinner"}]
        for payload in payloads:
            res = self.client.post("/v1/tags", json=payload)
            assert res.status_code == httpx.codes.CREATED

        res = self.client.get("/v1/tags")
        assert res.status_code == httpx.codes.OK

        payloads_sorted = sorted(payloads, key=lambda p: p["name"])
        tags = res.json()["data"]
        for idx, tag in enumerate(tags):
            assert tag["name"] == payloads_sorted[idx]["name"]

    def test_tag_recipe_count(self):
        """GET /v1/tags → tag on 2 recipes has recipe_count: 2"""
        recipe_payloads = [
            {
                "name": "Nasi Goreng",
                "description": "Indonesian fried rice with sweet soy sauce",
                "servings": 2,
                "prep_minutes": 10,
                "cook_minutes": 15,
                "difficulty": "easy",
                "ingredients": [
                    {"name": "cooked rice", "quantity": 400.000, "unit": "gram"},
                    {"name": "garlic", "quantity": 3.000, "unit": "cloves"},
                    {
                        "name": "sweet soy sauce",
                        "quantity": 2.000,
                        "unit": "tablespoon",
                    },
                    {"name": "egg", "quantity": 2.000, "unit": "pieces"},
                ],
                "instruction_steps": [
                    {"number": 1, "text": "Heat oil in wok over high heat"},
                    {"number": 2, "text": "Saute garlic until fragrant"},
                    {"number": 3, "text": "Add rice and stir-fry for 3 minutes"},
                    {"number": 4, "text": "Add sweet soy sauce and mix well"},
                    {
                        "number": 5,
                        "text": "Push rice aside, scramble eggs then mix together",
                    },
                ],
                "tags": ["indonesian", "rice", "quick"],
            },
            {
                "name": "Rendang Daging",
                "description": "Slow-cooked beef in coconut milk and spices",
                "servings": 6,
                "prep_minutes": 30,
                "cook_minutes": 180,
                "difficulty": "hard",
                "ingredients": [
                    {"name": "beef chuck", "quantity": 1000.000, "unit": "gram"},
                    {"name": "coconut milk", "quantity": 800.000, "unit": "ml"},
                    {"name": "lemongrass", "quantity": 3.000, "unit": "stalks"},
                    {"name": "galangal", "quantity": 50.000, "unit": "gram"},
                    {"name": "chili pepper", "quantity": 100.000, "unit": "gram"},
                ],
                "instruction_steps": [
                    {
                        "number": 1,
                        "text": "Blend spice paste from chili, galangal, garlic, shallots",
                    },
                    {"number": 2, "text": "Add beef and coconut milk to pot"},
                    {"number": 3, "text": "Add blended spice paste and lemongrass"},
                    {
                        "number": 4,
                        "text": "Cook on low heat for 3 hours, stirring occasionally",
                    },
                    {
                        "number": 5,
                        "text": "Continue until liquid reduces and oil separates",
                    },
                ],
                "tags": ["indonesian", "beef", "slow-cook"],
            },
        ]
        for rp in recipe_payloads:
            res = self.client.post("/v1/recipes", json=rp)
            assert res.status_code == httpx.codes.CREATED

        res = self.client.get("/v1/tags")
        assert res.status_code == httpx.codes.OK

        data = res.json()["data"]
        tags = [tag for tag in data if tag["recipe_count"] == 2]
        assert len(tags) > 0

    def test_orphan_tag_listed(self):
        """GET /v1/tags → tag with 0 recipes still listed with recipe_count: 0"""
        recipe_payload = {
            "name": "Nasi Goreng",
            "description": "Indonesian fried rice with sweet soy sauce",
            "servings": 2,
            "prep_minutes": 10,
            "cook_minutes": 15,
            "difficulty": "easy",
            "ingredients": [
                {"name": "cooked rice", "quantity": 400.000, "unit": "gram"},
                {"name": "garlic", "quantity": 3.000, "unit": "cloves"},
                {"name": "sweet soy sauce", "quantity": 2.000, "unit": "tablespoon"},
                {"name": "egg", "quantity": 2.000, "unit": "pieces"},
            ],
            "instruction_steps": [
                {"number": 1, "text": "Heat oil in wok over high heat"},
                {"number": 2, "text": "Saute garlic until fragrant"},
                {"number": 3, "text": "Add rice and stir-fry for 3 minutes"},
                {"number": 4, "text": "Add sweet soy sauce and mix well"},
                {
                    "number": 5,
                    "text": "Push rice aside, scramble eggs then mix together",
                },
            ],
            "tags": ["indonesian", "rice", "quick"],
        }
        res = self.client.post("/v1/recipes", json=recipe_payload)
        assert res.status_code == httpx.codes.CREATED

        tag_payload = {"name": "dinner"}
        res = self.client.post("/v1/tags", json=tag_payload)
        assert res.status_code == httpx.codes.CREATED

        res = self.client.get("/v1/tags")
        assert res.status_code == httpx.codes.OK
        data = res.json()["data"]
        tags = [tag for tag in data if tag["recipe_count"] == 0]
        assert len(tags) > 0

    def test_create_tag_empty_name(self):
        """POST /v1/tags with {"name": ""} → 422"""
        payload = {"name": ""}
        res = self.client.post("/v1/tags", json=payload)
        assert res.status_code == httpx.codes.UNPROCESSABLE_CONTENT

    def test_create_tag_long_name(self):
        """POST /v1/tags with 51-char name → 422"""
        payload = {"name": "a" * 51}
        res = self.client.post("/v1/tags", json=payload)
        assert res.status_code == httpx.codes.UNPROCESSABLE_CONTENT
