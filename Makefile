.PHONY: dev test

dev:
	uv run fastapi dev src/main.py

test:
	uv run pytest -vv

test-db:
	uv run pytest -vv -k "test_create
