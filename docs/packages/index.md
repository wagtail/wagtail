(packages_guide)=

# Packages

Wagtail benefits from a rich ecosystem of packages. Many Python and Django packages work with Wagtail out of the box, and there is a growing collection of Wagtail-specific packages for extending the CMS.

## Finding existing packages

The official [Wagtail third-party packages directory](https://wagtail.org/packages/) lists packages organized by category. Forms, migrations, media, integrations, SEO, and more. [Awesome Wagtail](https://github.com/springload/awesome-wagtail) offers a curated list of packages, articles, and resources.

Many general-purpose Django or Python packages also work directly, or can be integrated directly inside the CMS with little work. Check out the [Django Packages](https://djangopackages.org/) directory, or search directly on the [Python Package Index (PyPI)](https://pypi.org/). You can use the classifier [`Framework :: Wagtail`](https://pypi.org/search/?q=&o=&c=Framework+%3A%3A+Wagtail) to find packages that explicitly target Wagtail compatibility.

See [How to pick a good Wagtail package](https://wagtail.org/blog/pick-out-packages/) for more guidance on how to find and select packages.

## Creating packages

We recommend the [cookiecutter-wagtail-package](https://github.com/wagtail/cookiecutter-wagtail-package) template to scaffold a new package with a suitable structure, quality assurance tooling, and other important aspects of package authoring. We also provide guidelines for maintainers, to complement the official [Python Packaging User Guide](https://packaging.python.org/en/latest/).

To tag your package as compatible with Wagtail, use our official classifier: [`Framework :: Wagtail`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail). You can also add version-specific classifiers for all major versions, for example: `Framework :: Wagtail :: 6`.

## Package maintenance guidelines

We recommend these guidelines for all packages in our ecosystem. They are particularly important for packages that are part of the [first-party Wagtail packages](https://github.com/wagtail) and the [Wagtail Nest organization](https://github.com/wagtail-nest) for community-maintained packages.

### Fundamentals

- Consider naming your package with a `wagtail-` or `django-` prefix for ease of identification.
- Use an [OSI approved license](https://opensource.org/licenses), shared in a `LICENSE` file and with publication metadata. We recommend the [3-Clause BSD License](https://opensource.org/license/bsd-3-clause).

### Documentation

This is crucial to the success of your package.

- We recommend writing all documentation in vanilla Markdown ([CommonMark](https://commonmark.org/)), with minimal to no use of platform-specific extensions.
- Start with a README with basic information about all aspects of the package. Include:
    - Support targets for Python, Django, Wagtail.
    - Simple installation guide.
    - Links to all relevant resources about using or working on the package (documentation, support, security, changelog, etc.)
- Create separate files for all aspects of the package to be documented. We recommend the [Diátaxis](https://diataxis.fr/) documentation structure.
    - Produce reference documentation for all public APIs of the package.
    - Create how-to material for common usage scenarios.
    - Add a beginner tutorial for first-time users of the package.
    - Create a `CONTRIBUTING.md` guide for contributors.
- Consider publishing the package documentation as a website.

### Package metadata

Use the `pyproject.toml` format and standardized fields for as many aspects of the package as possible.

- Dependency versions should be as wide as possible.
- Support for EOL versions of Python, Django and Wagtail should be removed from the earliest minor release of the package following the moment the dependency went EOL. This does not apply if provision is made to maintain support for the EOL dependency.
- Use [optional dependency groups](https://packaging.python.org/en/latest/specifications/dependency-groups/) for development dependencies.
- Use classifiers for supported Python, Django, and Wagtail versions.
- Use [supported project URLs](https://docs.pypi.org/project_metadata/) to link to resources about the package.

# Quality assurance

- Set up linting and auto-formatting for Python code, Django templates, and other code where possible.
- Use [@wagtail/stylelint-config-wagtail](https://github.com/wagtail/stylelint-config-wagtail) for CSS linting, and [@wagtail/eslint-config-wagtail](https://github.com/wagtail/eslint-config-wagtail) for JS linting.
- Write unit tests using Django’s built-in test framework.
- Aim for unit test coverage above 90% (excluding migrations).
- Set up continuous integration to automatically test every change to the package.
- Consider setting up our recommended [nightly testing of official plugins](https://github.com/wagtail/wagtail/wiki/Nightly-testing-of-official-plugins).
- For packages that come with a user interface, follow the same accessibility standards as Wagtail. See [Wagtail’s accessibility statement](https://wagtail.org/accessibility/). Accessibility can be difficult to implement or test - reach out to [Wagtail’s accessibility team](https://github.com/wagtail/wagtail/wiki/Accessibility-team) to validate your approach or test the package.

### Releases

- Follow [Semantic Versioning](https://semver.org/) and [PEP 440 – Version Identification and Dependency Specification](https://peps.python.org/pep-0440/).
- Document changes in a `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) format.
- Use a git `vx.y.z` git tag in addition to publishing releases to PyPI.
- Use a `stable/x.y` branch when working on patch releases to previous versions.

### PyPI

- Make sure your package README correctly renders on its PyPI page.
- Share access with at least one or two other people to reduce the bus factor on maintainers.
- If your package is part of an organization, add it to the corresponding PyPI org (see [Wagtail on PyPI](https://pypi.org/org/wagtail/) and[Wagtail Nest on PyPI](https://pypi.org/org/wagtail-nest/)).

## EOL (End of Life) packages

Add a message to the package README, and visible on PyPI as well. For official packages, we additionally transfer them to the [wagtail-deprecated organization in GitHub](https://github.com/wagtail-deprecated) organisation.
