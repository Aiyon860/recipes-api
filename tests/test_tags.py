from tests.conftest import client


def test_create_tag(client):
    """POST /tags → 201, id + name returned"""
    pass


def test_duplicate_tag_409(client):
    """POST /tags with same name twice → 409"""
    pass


def test_list_tags(client):
    """GET /tags → returns all tags sorted by name"""
    pass


def test_tag_recipe_count(client):
    """GET /tags → tag on 2 recipes has recipe_count: 2"""
    pass


def test_orphan_tag_listed(client):
    """GET /tags → tag with 0 recipes still listed with recipe_count: 0"""
    pass


def test_create_tag_empty_name(client):
    """POST /tags with {"name": ""} → 422"""
    pass


def test_create_tag_long_name(client):
    """POST /tags with 51-char name → 422"""
    pass
