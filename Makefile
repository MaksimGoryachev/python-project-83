install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

build1: check
	poetry build

build:
	./build.sh

lint:
	poetry run flake8 page_analyzer

test:
	poetry run pytest

#test-coverage:
#	poetry run pytest --cov=page_analyzer --cov-report xml tests/

setup: install build

selfcheck:
	poetry check

check: selfcheck lint test

.PHONY: install test lint selfcheck check build start dev