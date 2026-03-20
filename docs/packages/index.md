(packages_guide)=

# Packages

Wagtail benefits from a rich ecosystem of packages. Many Python and Django packages work with Wagtail out of the box, and there is a growing collection of Wagtail-specific packages for extending the CMS.

## Finding existing packages

The official [Wagtail third-party packages directory](https://wagtail.org/packages/) lists packages organized by category. Forms, migrations, media, integrations, SEO, and more. [Awesome Wagtail](https://github.com/springload/awesome-wagtail) offers a curated list of packages, articles, and resources.

Many general-purpose Django or Python packages also work directly, or can be integrated directly inside the CMS with little work. Check out the [Django Packages](https://djangopackages.org/) directory, or search directly on the [Python Package Index (PyPI)](https://pypi.org/). You can use the classifier [`Framework :: Wagtail`](https://pypi.org/search/?q=&o=&c=Framework+%3A%3A+Wagtail) to find packages that explicitly target Wagtail compatibility.

See [How to pick a good Wagtail package](https://wagtail.org/blog/pick-out-packages/) for more guidance on how to find and select packages.

## Creating packages

We recommend the [cookiecutter-wagtail-package](https://github.com/wagtail/cookiecutter-wagtail-package) template to scaffold a new package with a suitable structure, quality assurance tooling, and other important aspects of package authoring.

To tag your package as compatible with Wagtail, use our official classifier: [`Framework :: Wagtail`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail). You can also add version-specific classifiers for all major versions, for example: `Framework :: Wagtail :: 6`.

## Package maintenance guidelines

We recommend these guidelines for all packages in our ecosystem. They are particularly important for packages that are part of the [first-party Wagtail packages](https://github.com/wagtail) and the [Wagtail Nest organization](https://github.com/wagtail-nest) for community-maintained packages.

# Documentation

## README

- Must be written in Markdown and named `README.md`.
- Must be visible on PyPI and render properly.
- Must mention what versions of Python, Django, Wagtail are supported.
- Must include "quick start" guidance, in particular for initial setup. This could be an abridged version of what is in separate documentation.
- Must link to the package’s documentation, CHANGELOG, PyPI page, discussion space
- Must link to the Github discussions board that should be enabled on the repo (see Support)
- Must mention where to report security issues (security@wagtail.org)

## Documentation

Note: Small packages may use their readme as documentation. These guidelines only apply when documentation separate to the readme exists.

- Must be available on the web
- Must be written in markdown
- Must be linked to from readme
- Must mention what versions of Python, Django and Wagtail are supported
- Must have an installation guide and a usage guide
- Should have reference or explanation, depending on the complexity of the package

## Changelog

- Must have a changelog named `CHANGELOG.md`
- Should follow Keep a Changelog

## Contributing guide

- Must have a contributing guide which is named `CONTRIBUTING.md`

## License

- Must have a permissive licence (such as BSD or MIT, but not GPL)
- Should be licensed under BSD 3-clause, if possible
- Must have a license file at the top of the repo

## `setup.py` / `setup.cfg` / `pyproject.toml`

- Dependency versions should be as wide as possible
- Support for EOL versions of Python, Django and Wagtail should be removed from the earliest minor release of the package following the moment the dependency went EOL. This does not apply if provision is made to maintain support for the EOL dependency.
- Testing and documentation requirements listed in extras
- Must have classifiers for Python, Django and Wagtail versions
- Must have classifier for license
- Must have project URLs linking to Documentation and Changelog

# Development Process

## Branching

- Default branch must be called `main`
- Each major release must have a branch prefixed with “stable”. For example `stable/1.0.x`. This is to allow security fixes to be backported

## Releases

- Version numbers must follow PEP440
- Each release must have a git tag and a github release
- Each release must be mentioned in the changelog
- Each release must be published to PyPI

## PyPI

- Package must have a PyPI page
- At least two core team members must have admin access
    - Note: Everyone who has permission to publish an official Wagtail package must have 2FA enabled on their PyPI account. Remember to check this when adding collaborators (this is visible in the PyPI web UI)

# Automated testing

## Django unit tests

- Should use Django’s built-in test framework
- Must have unit test coverage of at least 85%
- Should aim for unit test coverage of at least 90%
- Migrations and tests must be excluded from coverage reports
- Must have instructions on how to run unit tests

## Continuous Integration

- Must have a Continuous Integration set up with Github Actions, Circle CI, or both
- Should test against Wagtail nightly and report issues to #nightly-build-failures channel
- Must be linted with flake8
- Should be formatted with black and isort

## Support

- Should provide support through Github Discussions

## New packages

- For packages that come with a user interface, we expect those to adhere to the same accessibility standards as Wagtail. See [Wagtail’s accessibility statement](https://wagtail.org/accessibility/). Accessibility can be difficult to implement or test - reach out to [Wagtail’s accessibility team](https://github.com/wagtail/wagtail/wiki/Accessibility-team) to validate your approach or test the package.

## EOL (End of Life) packages

- The repository must be archived and moved to the [wagtail-deprecated](https://github.com/wagtail-deprecated) organisation
- A message must be added to the readme. This should be visible on both PyPI as well
