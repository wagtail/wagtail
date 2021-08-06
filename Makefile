.PHONY: clean-pyc develop spelling lint test coverage

help:
	@echo "clean-pyc - remove Python file artifacts"
	@echo "develop - install development dependencies"
	@echo "lint - check style with flake8"
	@echo "test - run tests"
	@echo "coverage - check code coverage"

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

develop: clean-pyc
	pip install -e .[testing,docs]
	npm install --no-save && npm run build

spelling:
	codespell -S *.po,*.map,*/vendor/*,*vendor.js*,./node_modules/*,./docs/_build/*,./storybook-static/*,./wagtail/admin/static/wagtailadmin/js/*,./package-lock.json

lint: spelling
	flake8
	isort --check-only --diff .
	# Filter out known false positives, while preserving normal output and error codes.
	# See https://github.com/motet-a/jinjalint/issues/18.
	jinjalint --parse-only wagtail | grep -v 'welcome_page.html:6:70' | tee /dev/tty | wc -l | grep -q '0'
	npm run lint:css --silent
	npm run lint:js --silent
	doc8 docs

test:
	python runtests.py

coverage:
	coverage run --source wagtail runtests.py
	coverage report -m
	coverage html
	open coverage_html_report/index.html
