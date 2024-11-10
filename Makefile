install:
		poetry install

dev:
		poetry run flask --app page_analyzer:app --debug run

PORT ?= 8000
start:
		poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build: check
		poetry build

lint:
		poetry run flake8 page_analyzer test

test:
		poetry run pytest

test-coverage:
		poetry run pytest --cov=page_analyzer --cov-report xml

setup: install build

selfcheck:
	poetry check

check: selfcheck test lint

.PHONY: install test lint selfcheck check build