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
	npm install --no-save && npm run build

lint:
	flake8 wagtail
	isort --check-only --diff --recursive wagtail
	# Filter out known false positives, while preserving normal output and error codes.
	# See https://github.com/motet-a/jinjalint/issues/18.
	jinjalint --parse-only wagtail | grep -v 'welcome_page.html:6:70' | tee /dev/tty | wc -l | grep -q '0'
	npm run lint:css --silent
	npm run lint:js --silent

test:
	python runtests.py

test-all:
	tox

coverage:
	coverage run --source wagtail setup.py
	coverage report -m
	coverage html
	open htmlcov/index.html
