(developing_for_wagtail)=

# Setting up a development environment

Setting up a local copy of [the Wagtail git repository](https://github.com/wagtail/wagtail) is slightly more involved than running a release package of Wagtail, as it requires [Node.js](https://nodejs.org/) and npm for building JavaScript and CSS assets. (This is not required when running a release version, as the compiled assets are included in the release package.)

If you're happy to develop on a local virtual machine, the [docker-wagtail-develop](https://github.com/wagtail/docker-wagtail-develop) and [vagrant-wagtail-develop](https://github.com/wagtail/vagrant-wagtail-develop) setup scripts are the fastest way to get up and running. They will provide you with a running instance of the [Wagtail Bakery demo site](https://github.com/wagtail/bakerydemo/), with the Wagtail and bakerydemo codebases available as shared folders for editing on your host machine.

You can also set up a cloud development environment that you can work with in a browser-based IDE using the [gitpod-wagtail-develop](https://github.com/wagtail/gitpod-wagtail-develop) project.

(Build scripts for other platforms would be very much welcomed - if you create one, please let us know via the [Slack workspace](https://github.com/wagtail/wagtail/wiki/Slack)!)

If you'd prefer to set up all the components manually, read on. These instructions assume that you're familiar with using pip and [virtual environments](inv:python#tutorial/venv) to manage Python packages.

## Setting up the Wagtail codebase

The preferred way to install the correct version of Node is to use [Fast Node Manager (fnm)](https://github.com/Schniz/fnm), which will always align the version with the supplied `.nvmrc` file in the root of the project. To ensure you are running the correct version of Node, run `fnm install` from the project root.
Alternatively, you can install [Node.js](https://nodejs.org/) directly, ensure you install the version as declared in the project's root `.nvmrc` file.

You will also need to install the **libjpeg** and **zlib** libraries, if you haven't done so already - see Pillow's [platform-specific installation instructions](https://pillow.readthedocs.io/en/stable/installation/building-from-source.html#external-libraries).

Fork [the Wagtail codebase](https://github.com/wagtail/wagtail) and clone the forked copy:

```sh
git clone https://github.com/username/wagtail.git
cd wagtail
```

**With your preferred [virtualenv activated](virtual_environment_creation),** install the Wagtail package in development mode with the included testing and documentation dependencies:

```sh
pip install -e ."[testing,docs]" --config-settings editable-mode=strict -U
```

Or, on Windows

```doscon
pip install -e .[testing,docs] --config-settings editable-mode=strict -U
```

Install the tool chain for building static assets:

```sh
npm ci
```

Compile the assets:

```sh
npm run build
```

Any Wagtail sites you start up in this virtualenv will now run against this development instance of Wagtail. We recommend using the [Wagtail Bakery demo site](https://github.com/wagtail/bakerydemo/) as a basis for developing Wagtail. Keep in mind that the setup steps for a Wagtail site may include installing a release version of Wagtail, which will override the development version you've just set up. In this case, to install the local Wagtail development instance in your virtualenv for your Wagtail site:

```sh
pip install -e path/to/wagtail"[testing,docs]" --config-settings editable-mode=strict -U
```

Or, on Windows

```doscon
pip install -e path/to/wagtail[testing,docs] --config-settings editable-mode=strict -U
```

Here, `path/to/wagtail` is the path to your local Wagtail copy.

(development_on_windows)=

## Development on Windows

Documentation for development on Windows has some gaps and should be considered a work in progress. We recommend setting up on a local virtual machine using our already available scripts, [docker-wagtail-develop](https://github.com/wagtail/docker-wagtail-develop) or [vagrant-wagtail-develop](https://github.com/wagtail/vagrant-wagtail-develop)

If you are confident with Python and Node development on Windows and wish to proceed here are some helpful tips.

We recommend [Chocolatey](https://chocolatey.org/install) for managing packages in Windows. Once Chocolatey is installed you can then install the [`make`](https://community.chocolatey.org/packages/make) utility in order to run common build and development commands.

We use LF for our line endings. To effectively collaborate with other developers on different operating systems, use Git's automatic CRLF handling by setting the `core.autocrlf` config to `true`:

```doscon
git config --global core.autocrlf true
```

(testing)=

## Testing

From the root of the Wagtail codebase, run the following command to run all the Python tests:

```sh
python runtests.py
```

### Running only some of the tests

At the time of writing, Wagtail has well over 5000 tests, which takes a while to
run. You can run tests for only one part of Wagtail by passing in the path as
an argument to `runtests.py` or `tox`:

```sh
# Running in the current environment
python runtests.py wagtail

# Running in a specified Tox environment
tox -e py39-dj32-sqlite-noelasticsearch -- wagtail

# See a list of available Tox environments
tox -l
```

You can also run tests for individual TestCases by passing in the path as
an argument to `runtests.py`

```sh
# Running in the current environment
python runtests.py wagtail.tests.test_blocks.TestIntegerBlock

# Running in a specified Tox environment
tox -e py39-dj32-sqlite-noelasticsearch -- wagtail.tests.test_blocks.TestIntegerBlock
```

### Running migrations for the test app models

You can create migrations for the test app by running the following from the Wagtail root.

```sh
django-admin makemigrations --settings=wagtail.test.settings
```

### Testing against PostgreSQL

```{note}
In order to run these tests, you must install the required modules for PostgreSQL as described in Django's [Databases documentation](inv:django#ref/databases).
```

By default, Wagtail tests against SQLite. You can switch to using PostgreSQL by
using the `--postgres` argument:

```sh
python runtests.py --postgres
```

If you need to use a different user, password, host, or port, use the `PGUSER`, `PGPASSWORD`, `PGHOST`, and `PGPORT` environment variables respectively.

### Testing against a different database

```{note}
In order to run these tests, you must install the required client libraries and modules for the given database as described in Django's [Databases documentation](inv:django#ref/databases) or the 3rd-party database backend's documentation.
```

If you need to test against a different database, set the `DATABASE_ENGINE`
environment variable to the name of the Django database backend to test against:

```sh
DATABASE_ENGINE=django.db.backends.mysql python runtests.py
```

This will create a new database called `test_wagtail` in MySQL and run
the tests against it.

If you need to use different connection settings, use the following environment variables which correspond to the respective keys within Django's [`DATABASES`](inv:django#DATABASES) settings dictionary:

-   `DATABASE_ENGINE`
-   `DATABASE_NAME`
-   `DATABASE_PASSWORD`
-   `DATABASE_HOST`
    -   Note that for MySQL, this must be `127.0.0.1` rather than `localhost` if you need to connect using a TCP socket
-   `DATABASE_PORT`

It is also possible to set `DATABASE_DRIVER`, which corresponds to the `driver` value within `OPTIONS` if an SQL Server engine is used.

### Testing Elasticsearch and OpenSearch

You can test Wagtail against Elasticsearch or OpenSearch by passing one of the arguments `--elasticsearch7`, `--elasticsearch8`, `--elasticsearch9`, `--opensearch2`, `--opensearch3` (corresponding to the version of Elasticsearch or OpenSearch you want to test against):

```sh
python runtests.py --elasticsearch8
```

Wagtail will attempt to connect to a local instance of Elasticsearch or OpenSearch
(`http://localhost:9200`) and use the index `test_wagtail`.

If your instance is located somewhere else, you can set the
`ELASTICSEARCH_URL` environment variable to point to its location:

```sh
ELASTICSEARCH_URL=https://my-elasticsearch-instance:9200 python runtests.py --elasticsearch8
```

Note that the environment variable `ELASTICSEARCH_URL` is used for both Elasticsearch and OpenSearch.

### Unit tests for JavaScript

We use [Jest](https://jestjs.io/) for unit tests of client-side business logic or UI components. From the root of the Wagtail codebase, run the following command to run all the front-end unit tests:

```sh
npm run test:unit
```

### Integration tests

Our end-to-end browser testing suite also uses [Jest](https://jestjs.io/), combined with [Puppeteer](https://pptr.dev/). We set this up to be installed separately so as not to increase the installation size of the existing Node tooling. To run the tests, you will need to install the dependencies and, in a separate terminal, run the test suite’s Django development server:

```sh
export DJANGO_SETTINGS_MODULE=wagtail.test.settings_ui
# Assumes the current environment contains a valid installation of Wagtail for local development.
./wagtail/test/manage.py migrate
./wagtail/test/manage.py createcachetable
DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=changeme ./wagtail/test/manage.py createsuperuser --noinput
./wagtail/test/manage.py runserver 0:8000
# In a separate terminal:
npm --prefix client/tests/integration install
npm run test:integration
```

Integration tests target `http://127.0.0.1:8000` by default. Use the `TEST_ORIGIN` environment variable to use a different port, or test a remote Wagtail instance: `TEST_ORIGIN=http://127.0.0.1:9000 npm run test:integration`.


## Compiling static assets

All static assets such as JavaScript, CSS, images, and fonts for the Wagtail admin are compiled from their respective sources by Webpack. The compiled assets are not committed to the repository, and are compiled before packaging each new release. Compiled assets should not be submitted as part of a pull request.

To compile the assets, run:

```sh
npm run build
```

This must be done after every change to the source files. To watch the source files for changes and then automatically recompile the assets, run:

```sh
npm start
```

## Compiling the documentation

The Wagtail documentation is built by Sphinx. To install Sphinx and compile the documentation, run:

```sh
# Starting from the wagtail root directory:

# Install the documentation dependencies
pip install -e .[docs] --config-settings editable-mode=strict
# or if using zsh as your shell:
#    pip install -e '.[docs]' -U
# Compile the docs
cd docs/
make html
```

The compiled documentation will now be in `docs/_build/html`.
Open this directory in a web browser to see it.
Python comes with a module that makes it very easy to preview static files in a web browser.
To start this simple server, run the following commands:

```sh
# Starting from the wagtail root directory:

cd docs/_build/html/
python -m http.server 8080
```

Now you can open <http://localhost:8080/> in your web browser to see the compiled documentation.

Sphinx caches the built documentation to speed up subsequent compilations.
Unfortunately, this cache also hides any warnings thrown by unmodified documentation source files.
To clear the built HTML and start fresh, so you can see all warnings thrown when building the documentation, run:

```sh
# Starting from the wagtail root directory:

cd docs/
make clean
make html
```

Wagtail also provides a way for documentation to be compiled automatically on each change.
To do this, you can run the following command to see the changes automatically at `localhost:4000`:

```sh
# Starting from the wagtail root directory:

cd docs/
make livehtml
```

(linting_and_formatting)=
## Linting and formatting

Wagtail makes use of various tools to ensure consistency and readability across the codebase:

- [Ruff](https://github.com/astral-sh/ruff) for formatting and linting Python code, including enforcing [PEP8](https://peps.python.org/pep-0008/) and [isort](https://pycqa.github.io/isort/) rules
- [djhtml](https://github.com/rtts/djhtml) and [Curlylint](https://www.curlylint.org/) for formatting and linting HTML templates
- [Prettier](https://prettier.io/), [Stylelint](https://stylelint.io/) and [ESLint](https://eslint.org/) for formatting and linting JavaScript and CSS code

All contributions should follow these standards, and you are encouraged to run these tools locally to avoid delays in your contributions being accepted. Here are the available commands:

-   `make lint` will run all linting, `make lint-server` lints Python and template code, and `make lint-client` lints JS/CSS.
-   `make format` will run all formatting and fixing of linting issues. There is also `make format-server` and `make format-client`.

Have a look at our `Makefile` tasks and `package.json` scripts if you prefer more granular options.

### Automatically lint and code format on commits

[pre-commit](https://pre-commit.com/) is configured to automatically run code linting and formatting checks with every commit. To install pre-commit into your git hooks run:

```sh
pre-commit install
```

pre-commit should now run on every commit you make.

(developing_using_a_fork)=

## Using forks for installation

Sometimes it may be necessary to install Wagtail from a fork. For example your site depends on a bug fix that is currently waiting for review, and you cannot afford waiting for a new release.

The Wagtail release process includes steps for static asset building and translations updated which means you cannot update your requirements file to point a particular git commit in the main repository.

To install from your fork, ensure you have installed `build` (`python -m pip install build`) and the tooling for building the static assets (`npm install`). Then, from the root of your Wagtail git checkout, run:

```sh
python -m build
```

This will create a `.tar.gz` and `.whl` packages within `dist/,` which can be installed with `pip`.

For remote deployments, it's usually most convenient to upload this to a public URL somewhere and place that URL in your project's requirements in place of the standard `wagtail` line.
