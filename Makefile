install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

build: check
	poetry build

publish:
	poetry publish --dry-run

package-install:
	python3 -m pip install dist/*.whl

lint:
	poetry run flake8 gendiff tests

test:
	poetry run pytest

test-coverage:
	poetry run pytest --cov=gendiff --cov-report xml tests/

package-reinstall:
	python3 -m pip install --force-reinstall dist/*.whl

setup: install build package-install

selfcheck:
	poetry check

check: selfcheck test lint

.PHONY: install test lint selfcheck check build