.PHONY: clean-pyc develop lint test coverage

help:
	@echo "clean-pyc - remove Python file artifacts"
	@echo "develop - install development dependencies"
	@echo "lint - check style with black, flake8, sort python with isort, indent html, and lint frontend css/js"
	@echo "format - enforce a consistent code style across the codebase, sort python files with isort and fix frontend css/js"
	@echo "test - run tests"
	@echo "coverage - check code coverage"

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

develop: clean-pyc
	pip install -e .[testing,docs]
	npm install --no-save && npm run build

lint-server:
	black --target-version py37 --check --diff .
	flake8
	isort --check-only --diff .
	curlylint --parse-only wagtail
	git ls-files '*.html' | xargs djhtml --check

lint-client:
	npm run lint:css --silent
	npm run lint:js --silent
	npm run lint:format --silent

lint-docs:
	doc8 docs

lint: lint-server lint-client lint-docs

format-server:
	black --target-version py37 .
	isort .
	git ls-files '*.html' | xargs djhtml -i

format-client:
	npm run format
	npm run fix:js

format: format-server format-client

test:
	python runtests.py

coverage:
	coverage run --source wagtail runtests.py
	coverage report -m
	coverage html
	open coverage_html_report/index.html
