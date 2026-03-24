# Development
format-all:
	@isort fastexec tests
	@black fastexec tests

install-all:
	poetry install --all-extras --all-groups

update-all:
	poetry update
	poetry export --without-hashes -f requirements.txt --output requirements.txt
	poetry export --without-hashes -f requirements.txt --output requirements-all.txt --all-extras --all-groups

# Docs
mkdocs:
	mkdocs serve

# Tests
pytest:
	python -m pytest
