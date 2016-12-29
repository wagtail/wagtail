.PHONY: clean-pyc develop

help:
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "coverage - check code coverage quickly with the default Python"

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

develop: clean-pyc
	pip install -e .[testing,docs]
	npm install && npm run build

lint:
	flake8 wagtail
	isort --check-only --diff --recursive wagtail

test:
	python runtests.py

test-all:
	tox

coverage:
	coverage run --source wagtail setup.py
	coverage report -m
	coverage html
	open htmlcov/index.html
