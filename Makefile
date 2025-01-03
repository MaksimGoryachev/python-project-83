install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build:
	./build.sh

lint1:
	poetry run flake8 page_analyzer

ruff:
	poetry run ruff check page_analyzer

fix:
	poetry run ruff check --fix page_analyzer

lint: lint1 ruff

setup: install build

selfcheck:
	poetry check

check: selfcheck lint

.PHONY: install lint1 lint selfcheck check build start dev setup fix