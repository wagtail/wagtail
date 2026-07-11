# Wagtail development tasks, run with https://github.com/casey/just
#
# Run `just` (or `just --list`) to see all available recipes.

# List all available recipes
default:
    @just --list

# --- Setup ---------------------------------------------------------------

# Install Python and Node development dependencies and build static assets
[group('setup')]
develop: clean-pyc
    pip install -e .[testing,docs] --config-settings editable-mode=strict
    npm install --no-save
    npm run build

# Remove compiled Python file artifacts
[group('setup')]
clean-pyc:
    find . -name '*.pyc' -exec rm -f {} +
    find . -name '*.pyo' -exec rm -f {} +
    find . -name '*~' -exec rm -f {} +

# --- Lint ----------------------------------------------------------------

# Run all linting (Python, templates, frontend, and docs)
[group('lint')]
lint: lint-server lint-client lint-docs

# Lint Python and template code
[group('lint')]
lint-server:
    ruff format --check .
    ruff check .
    ty check
    curlylint --parse-only wagtail
    git ls-files '*.html' | xargs djhtml --check
    semgrep --config .semgrep.yml --error .

# Lint frontend JavaScript and CSS
[group('lint')]
lint-client:
    npm run lint --loglevel silent

# Lint the documentation
[group('lint')]
lint-docs:
    doc8 docs

# --- Format --------------------------------------------------------------

# Format and auto-fix all code (Python, templates, and frontend)
[group('format')]
format: format-server format-client

# Format and auto-fix Python and template code
[group('format')]
format-server:
    ruff check . --fix
    ruff format .
    git ls-files '*.html' | xargs djhtml

# Format and auto-fix frontend JavaScript and CSS
[group('format')]
format-client:
    npm run format
    npm run fix:js

# --- Test ----------------------------------------------------------------

# Run the Python test suite (pass extra args, e.g. `just test wagtail.admin`)
[group('test')]
test *args:
    python runtests.py {{ args }}

# Run the frontend unit tests
[group('test')]
test-client:
    npm run test:unit

# Measure Python test coverage and write an HTML report
[group('test')]
coverage:
    coverage run --source wagtail runtests.py
    coverage report -m
    coverage html
    @echo "HTML coverage report written to coverage_html_report/index.html"

# --- Build ---------------------------------------------------------------

# Compile the frontend static assets for the admin
[group('build')]
build:
    npm run build

# Watch and recompile the frontend static assets on change
[group('build')]
watch:
    npm start

# --- Docs ----------------------------------------------------------------

# Build the documentation as HTML in docs/_build/html
[group('docs')]
docs:
    sphinx-build -b html --fail-on-warning -n -jauto -d docs/_build/doctrees docs docs/_build/html

# Serve the documentation locally with live rebuilds on http://localhost:4000
[group('docs')]
docs-serve:
    sphinx-autobuild --port 4000 --host 0.0.0.0 -b html -W -n -jauto -d docs/_build/doctrees docs docs/_build/html

# --- API -----------------------------------------------------------------

# Regenerate the v3 API OpenAPI snapshot for CI
[group('api')]
openapi-snapshot:
    DJANGO_SETTINGS_MODULE=wagtail.test.settings python -c 'import json, django; django.setup(); from wagtail.api.v3.api import api; from ninja.responses import NinjaJSONEncoder; f = open("wagtail/api/v3/tests/snapshots/openapi.json", "w"); json.dump(api.get_openapi_schema(), f, cls=NinjaJSONEncoder, indent=2, sort_keys=True); f.write("\n"); f.close()'
