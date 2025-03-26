.PHONY: clean-pyc develop lint-server lint-client lint-docs lint format-server format-client format test coverage

help:
	@echo "clean-pyc - remove Python file artifacts"
	@echo "develop - install development dependencies"
	@echo "lint - check style with ruff, sort python with ruff, indent html, and lint frontend css/js"
	@echo "format - enforce a consistent code style across the codebase, sort python files with ruff and fix frontend css/js"
	@echo "test - run tests"
	@echo "coverage - check code coverage"

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

develop: clean-pyc
	pip install -e .[testing,docs] --config-settings editable-mode=strict
	npm install --no-save && npm run build

lint-server:
	ruff format --check .
	ruff check .
	curlylint --parse-only wagtail
	git ls-files '*.html' | xargs djhtml --check
	semgrep --config .semgrep.yml --error .

lint-client:
	npm run lint:css --silent
	npm run lint:js --silent
	npm run lint:format --silent

lint-docs:
	doc8 docs

lint: lint-server lint-client lint-docs

format-server:
	ruff check . --fix
	ruff format .
	git ls-files '*.html' | xargs djhtml

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
