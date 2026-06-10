# Development
fmt:
	@isort fastexec tests
	@black fastexec tests
	@ruff check --fix fastexec tests

install:
	pip install -e ".[dev,docs]"

update:
	poetry update

# Docs
mkdocs:
	mkdocs serve

# Tests
pytest:
	python -m pytest
