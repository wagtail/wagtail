.PHONY: clean-pyc

help:
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "lint-js - check Javascript with airbnb"
	@echo "format-js - conform the project Javascript to airbnb"
	@echo "test - run tests quickly with the default Python"
	@echo "coverage - check code coverage quickly with the default Python"

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 wagtail

lint-js:
	npm run lint:js

format-js:
	npm run format:js

test:
	python runtests.py

test-all:
	tox

coverage:
	coverage run --source wagtail setup.py
	coverage report -m
	coverage html
	open htmlcov/index.html
