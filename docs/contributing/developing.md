(developing_for_wagtail)=

# Development

Setting up a local copy of [the Wagtail git repository](https://github.com/wagtail/wagtail) is slightly more involved than running a release package of Wagtail, as it requires [Node.js](https://nodejs.org/) and npm for building JavaScript and CSS assets. (This is not required when running a release version, as the compiled assets are included in the release package.)

If you're happy to develop on a local virtual machine, the [docker-wagtail-develop](https://github.com/wagtail/docker-wagtail-develop) and [vagrant-wagtail-develop](https://github.com/wagtail/vagrant-wagtail-develop) setup scripts are the fastest way to get up and running. They will provide you with a running instance of the [Wagtail Bakery demo site](https://github.com/wagtail/bakerydemo/), with the Wagtail and bakerydemo codebases available as shared folders for editing on your host machine.

You can also set up a cloud development environment that you can work with in a browser-based IDE using the [gitpod-wagtail-develop](https://github.com/wagtail/gitpod-wagtail-develop) project.

(Build scripts for other platforms would be very much welcomed - if you create one, please let us know via the [Slack workspace](https://github.com/wagtail/wagtail/wiki/Slack)!)

If you'd prefer to set up all the components manually, read on. These instructions assume that you're familiar with using pip and [virtual environments](https://docs.python.org/3/tutorial/venv.html) to manage Python packages.

## Setting up the Wagtail codebase

The preferred way to install the correct version of Node is to use [Node Version Manager (nvm)](https://github.com/nvm-sh/nvm) or [Fast Node Manager (fnm)](https://github.com/Schniz/fnm), which will always align the version with the supplied `.nvmrc` file in the root of the project. To ensure you are running the correct version of Node, run `nvm install` or `fnm install` from the project root.
Alternatively, you can install [Node.js](https://nodejs.org/) directly, ensure you install the version as declared in the project's root `.nvmrc` file.

You will also need to install the **libjpeg** and **zlib** libraries, if you haven't done so already - see Pillow's [platform-specific installation instructions](https://pillow.readthedocs.io/en/stable/installation.html#external-libraries).

Clone a copy of [the Wagtail codebase](https://github.com/wagtail/wagtail):

```sh
git clone https://github.com/wagtail/wagtail.git
cd wagtail
```

**With your preferred virtualenv activated,** install the Wagtail package in development mode with the included testing and documentation dependencies:

```sh
pip install -e '.[testing,docs]' -U
```

Install the tool chain for building static assets:

```sh
npm ci
```

Compile the assets:

```sh
npm run build
```

Any Wagtail sites you start up in this virtualenv will now run against this development instance of Wagtail. We recommend using the [Wagtail Bakery demo site](https://github.com/wagtail/bakerydemo/) as a basis for developing Wagtail. Keep in mind that the setup steps for a Wagtail site may include installing a release version of Wagtail, which will override the development version you've just set up. In this case, you should install the site before running the `pip install -e` step, or re-run that step after the site is installed.

(testing)=

## Testing

From the root of the Wagtail codebase, run the following command to run all the Python tests:

```sh
python runtests.py
```

### Running only some of the tests

At the time of writing, Wagtail has well over 2500 tests, which takes a while to
run. You can run tests for only one part of Wagtail by passing in the path as
an argument to `runtests.py` or `tox`:

```sh
# Running in the current environment
python runtests.py wagtail

# Running in a specified Tox environment
tox -e py39-dj32-sqlite-noelasticsearch wagtail

# See a list of available Tox environments
tox -l
```

You can also run tests for individual TestCases by passing in the path as
an argument to `runtests.py`

```sh
# Running in the current environment
python runtests.py wagtail.tests.test_blocks.TestIntegerBlock

# Running in a specified Tox environment
tox -e py39-dj32-sqlite-noelasticsearch wagtail.tests.test_blocks.TestIntegerBlock
```

### Running migrations for the test app models

You can create migrations for the test app by running the following from the Wagtail root.

```sh
django-admin makemigrations --settings=wagtail.test.settings
```

### Testing against PostgreSQL

```{note}
In order to run these tests, you must install the required modules for PostgreSQL as described in Django's [Databases documentation](https://docs.djangoproject.com/en/stable/ref/databases/).
```

By default, Wagtail tests against SQLite. You can switch to using PostgreSQL by
using the `--postgres` argument:

```sh
python runtests.py --postgres
```

If you need to use a different user, password, host, or port, use the `PGUSER`, `PGPASSWORD`, `PGHOST`, and `PGPORT` environment variables respectively.

### Testing against a different database

```{note}
In order to run these tests, you must install the required client libraries and modules for the given database as described in Django's [Databases documentation](https://docs.djangoproject.com/en/stable/ref/databases/) or the 3rd-party database backend's documentation.
```

If you need to test against a different database, set the `DATABASE_ENGINE`
environment variable to the name of the Django database backend to test against:

```sh
DATABASE_ENGINE=django.db.backends.mysql python runtests.py
```

This will create a new database called `test_wagtail` in MySQL and run
the tests against it.

If you need to use different connection settings, use the following environment variables which correspond to the respective keys within Django's [DATABASES](https://docs.djangoproject.com/en/stable/ref/settings/#databases) settings dictionary:

-   `DATABASE_ENGINE`
-   `DATABASE_NAME`
-   `DATABASE_PASSWORD`
-   `DATABASE_HOST`
    -   Note that for MySQL, this must be `127.0.0.1` rather than `localhost` if you need to connect using a TCP socket
-   `DATABASE_PORT`

It is also possible to set `DATABASE_DRIVER`, which corresponds to the `driver` value within `OPTIONS` if an SQL Server engine is used.

### Testing Elasticsearch

You can test Wagtail against Elasticsearch by passing the `--elasticsearch`
argument to `runtests.py`:

```sh
python runtests.py --elasticsearch
```

Wagtail will attempt to connect to a local instance of Elasticsearch
(`http://localhost:9200`) and use the index `test_wagtail`.

If your Elasticsearch instance is located somewhere else, you can set the
`ELASTICSEARCH_URL` environment variable to point to its location:

```sh
ELASTICSEARCH_URL=http://my-elasticsearch-instance:9200 python runtests.py --elasticsearch
```

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

Integration tests target `http://localhost:8000` by default. Use the `TEST_ORIGIN` environment variable to use a different port, or test a remote Wagtail instance: `TEST_ORIGIN=http://localhost:9000 npm run test:integration`.

### Browser and device support

Wagtail is meant to be used on a wide variety of devices and browsers. Supported browser / device versions include:

| Browser       | Device/OS  | Version(s) |
| ------------- | ---------- | ---------- |
| Mobile Safari | iOS Phone  | Last 2     |
| Mobile Safari | iOS Tablet | Last 2     |
| Chrome        | Android    | Last 2     |
| Chrome        | Desktop    | Last 2     |
| MS Edge       | Windows    | Last 2     |
| Firefox       | Desktop    | Latest     |
| Firefox ESR   | Desktop    | Latest     |
| Safari        | macOS      | Last 3     |

We aim for Wagtail to work in those environments, there are known support gaps for Safari 13 introduced in Wagtail 4.0 to provide better support for RTL languages. Our development standards ensure that the site is usable on other browsers **and will work on future browsers**.

IE 11 support has been officially dropped in 2.15 as it is gradually falling out of use. Features already known not to work include:

-   Rich text copy-paste in the rich text editor.
-   Sticky toolbar in the rich text editor.
-   Focus outline styles in the main menu & explorer menu.
-   Keyboard access to the actions in page listing tables.

**Unsupported browsers / devices include:**

| Browser       | Device/OS | Version(s) |
| ------------- | --------- | ---------- |
| Stock browser | Android   | All        |
| IE            | Desktop   | All        |
| Safari        | Windows   | All        |

### Accessibility targets

We want to make Wagtail accessible for users of a wide variety of assistive technologies. The specific standard we aim for is [WCAG2.1](https://www.w3.org/TR/WCAG21/), AA level. Here are specific assistive technologies we aim to test for, and ultimately support:

-   [NVDA](https://www.nvaccess.org/download/) on Windows with Firefox ESR
-   [VoiceOver](https://support.apple.com/en-gb/guide/voiceover-guide/welcome/web) on macOS with Safari
-   [Windows Magnifier](https://support.microsoft.com/en-gb/help/11542/windows-use-magnifier) and macOS Zoom
-   Windows Speech Recognition and macOS Dictation
-   Mobile [VoiceOver](https://support.apple.com/en-gb/guide/voiceover-guide/welcome/web) on iOS, or [TalkBack](https://support.google.com/accessibility/android/answer/6283677?hl=en-GB) on Android
-   Windows [High-contrast mode](https://support.microsoft.com/en-us/windows/use-high-contrast-mode-in-windows-10-fedc744c-90ac-69df-aed5-c8a90125e696)

We aim for Wagtail to work in those environments. Our development standards ensure that the site is usable with other assistive technologies. In practice, testing with assistive technology can be a daunting task that requires specialised training – here are tools we rely on to help identify accessibility issues, to use during development and code reviews:

-   [react-axe](https://github.com/dequelabs/react-axe) integrated directly into our build tools, to identify actionable issues. Logs its results in the browser console.
-   [@wordpress/jest-puppeteer-axe](https://github.com/WordPress/gutenberg/tree/trunk/packages/jest-puppeteer-axe) running Axe checks as part of integration tests.
-   [Axe](https://chrome.google.com/webstore/detail/axe/lhdoppojpmngadmnindnejefpokejbdd) Chrome extension for more comprehensive automated tests of a given page.
-   [Accessibility Insights for Web](https://accessibilityinsights.io/docs/en/web/overview) Chrome extension for semi-automated tests, and manual audits.

### Known accessibility issues

Wagtail’s administration interface isn’t fully accessible at the moment. We actively work on fixing issues both as part of ongoing maintenance and bigger overhauls. To learn about known issues, check out:

-   The [WCAG2.1 AA for CMS admin](https://github.com/wagtail/wagtail/projects/5) issues backlog.
-   Our [2021 accessibility audit](https://docs.google.com/spreadsheets/d/1l7tnpEyJiC5BWE_JX0XCkknyrjxYA5T2aee5JgPnmi4/edit).

The audit also states which parts of Wagtail have and haven’t been tested, how issues affect WCAG 2.1 compliance, and the likely impact on users.

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

## Using the pattern library

Wagtail’s UI component library is built with [Storybook](https://storybook.js.org/) and [django-pattern-library](https://github.com/torchbox/django-pattern-library). To run it locally,

```sh
export DJANGO_SETTINGS_MODULE=wagtail.test.settings_ui
# Assumes the current environment contains a valid installation of Wagtail for local development.
./wagtail/test/manage.py migrate
./wagtail/test/manage.py createcachetable
./wagtail/test/manage.py runserver 0:8000
# In a separate terminal:
npm run storybook
```

The last command will start Storybook at `http://localhost:6006/`. It will proxy specific requests to Django at `http://localhost:8000` by default. Use the `TEST_ORIGIN` environment variable to use a different port for Django: `TEST_ORIGIN=http://localhost:9000 npm run storybook`.

## Compiling the documentation

The Wagtail documentation is built by Sphinx. To install Sphinx and compile the documentation, run:

```sh
cd /path/to/wagtail
# Install the documentation dependencies
pip install -e .[docs]
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
cd docs/_build/html/
python -m http.server 8080
```

Now you can open <http://localhost:8080/> in your web browser to see the compiled documentation.

Sphinx caches the built documentation to speed up subsequent compilations.
Unfortunately, this cache also hides any warnings thrown by unmodified documentation source files.
To clear the built HTML and start fresh, so you can see all warnings thrown when building the documentation, run:

```sh
cd docs/
make clean
make html
```

Wagtail also provides a way for documentation to be compiled automatically on each change.
To do this, you can run the following command to see the changes automatically at `localhost:4000`:

```sh
cd docs/
make livehtml
```

## Automatically lint and code format on commits

[pre-commit](https://pre-commit.com/) is configured to automatically run code linting and formatting checks with every commit. To install pre-commit into your git hooks run:

```sh
pre-commit install
```

pre-commit should now run on every commit you make.
