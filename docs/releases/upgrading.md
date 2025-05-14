# Upgrading Wagtail

New feature releases of Wagtail are released every three months. These releases provide new features, improvements and bugfixes, and are marked by incrementing the second part of the version number (for example, 6.2 to 6.3).

Additionally, patch releases will be issued as needed, to fix bugs and security issues. These are marked by incrementing the third part of the version number (for example, 6.3 to 6.3.1).

Occasionally, feature releases include significant visual changes to the editor interface or backwards-incompatible changes. In these cases, the first part of the version number will be incremented (for example, 5.2 to 6.0).

For dates of past and upcoming releases and support periods, see [Release schedule](https://github.com/wagtail/wagtail/wiki/Release-schedule).

## Required reading

If it’s your first time doing an upgrade, it is highly recommended to read the
guide on [](release_process).

## Upgrade process

We recommend upgrading one feature release at a time, even if your project is several versions behind the current one. For example, instead of going from 6.0 directly to 6.3, upgrade to 6.1 and 6.2 first. This has a number of advantages over skipping directly to the newest release:

-   If anything breaks as a result of the upgrade, you will know which version caused it, and will be able to troubleshoot accordingly;
-   Deprecation warnings shown in the console output will notify you of any code changes you need to make before upgrading to the following version;
-   Some releases make database schema changes that need to be reflected on your project by running `./manage.py makemigrations` - this is liable to fail if too many schema changes happen in one go.

With that in mind, follow these steps for each feature release you need to upgrade to.

### Resolve deprecation warnings

When Wagtail makes a backwards-incompatible change to a publicly-documented feature in a release, it will continue to work in that release, but a deprecation warning will be raised when that feature is used. These warnings are intended to give you advance notice before the support is completely removed in a future release, so that you can update your code accordingly.

In Python, deprecation warnings are silenced by default. You must turn them on using the `-Wa` Python command line option or the `PYTHONWARNINGS` environment variable. For example, to show warnings while running tests:

```sh
python -Wa manage.py test
```

If you’re not using the Django test runner, you may need to also ensure that any console output is not captured which would hide deprecation warnings. For example, if you use [pytest](https://docs.pytest.org):

```sh
PYTHONWARNINGS=always pytest tests --capture=no
```

Resolve any deprecation warnings with your current version of Wagtail before continuing the upgrade process.

Third party packages might use deprecated APIs in order to support multiple versions of Wagtail, so deprecation warnings in packages you’ve installed don’t necessarily indicate a problem. If a package doesn’t support the latest version of Wagtail, consider raising an issue or sending a pull request to that package.

### Preparing for the upgrade

After resolving the deprecation warnings, you should read the [release notes](../releases/index) for the next feature release after your current Wagtail version.

Pay particular attention to the upgrade considerations sections (which describe any backwards-incompatible changes) to get a clear idea of what will be needed for a successful upgrade.

Also read the [](compatible_django_python_versions) table below, as they may
need upgrading first.

Before continuing with the upgrade, make a backup of your database.

### Upgrading

To upgrade:

-   Update the `wagtail` line in your project's `requirements.txt` file (or the equivalent, such as `pyproject.toml`) to specify the latest patch release of the version you wish to install. For example, to upgrade to version 6.3.x, the line should read:

        wagtail>=6.3,<6.4

-   Run:

        pip install -r requirements.txt
        ./manage.py makemigrations
        ./manage.py migrate

-   Make any necessary code changes as directed in the "Upgrade considerations" section of the release notes.
-   Test that your project is working as expected.

Remember that the JavaScript and CSS files used in the Wagtail admin may have changed between releases - if you encounter erratic behavior on upgrading, ensure that you have cleared your browser cache. When deploying the upgrade to a production server, be sure to run `./manage.py collectstatic` to make the updated static files available to the web server. In production, we recommend enabling {class}`~django.contrib.staticfiles.storage.ManifestStaticFilesStorage` in the [`STORAGES["staticfiles"]` setting](inv:django#STORAGES) - this ensures that different versions of files are assigned distinct URLs.

### Repeat

Repeat the above steps for each feature release you need to upgrade to.

(compatible_django_python_versions)=

## Compatible Django / Python versions

New feature releases frequently add support for newer versions of Django and Python, and drop support for older ones. We recommend always carrying out upgrades to Django and Python as a separate step from upgrading Wagtail.

The compatible versions of Django and Python for each Wagtail release are:

| Wagtail release | Compatible Django versions | Compatible Python versions  |
| --------------- | -------------------------- | --------------------------- |
| 7.1             | 4.2, 5.1, 5.2              | 3.9, 3.10, 3.11, 3.12, 3.13 |
| 7.0 LTS         | 4.2, 5.1, 5.2              | 3.9, 3.10, 3.11, 3.12, 3.13 |
| 6.4             | 4.2, 5.0, 5.1, 5.2         | 3.9, 3.10, 3.11, 3.12, 3.13 |
| 6.3 LTS         | 4.2, 5.0, 5.1, 5.2[^*]     | 3.9, 3.10, 3.11, 3.12, 3.13 |
| 6.2             | 4.2, 5.0                   | 3.8, 3.9, 3.10, 3.11, 3.12  |
| 6.1             | 4.2, 5.0                   | 3.8, 3.9, 3.10, 3.11, 3.12  |
| 6.0             | 4.2, 5.0                   | 3.8, 3.9, 3.10, 3.11, 3.12  |
| 5.2 LTS         | 3.2, 4.1, 4.2, 5.0[^*]     | 3.8, 3.9, 3.10, 3.11, 3.12  |
| 5.1             | 3.2, 4.1, 4.2              | 3.8, 3.9, 3.10, 3.11        |
| 5.0             | 3.2, 4.1, 4.2              | 3.7, 3.8, 3.9, 3.10, 3.11   |
| 4.2             | 3.2, 4.0, 4.1              | 3.7, 3.8, 3.9, 3.10, 3.11   |
| 4.1 LTS         | 3.2, 4.0, 4.1              | 3.7, 3.8, 3.9, 3.10, 3.11   |
| 4.0             | 3.2, 4.0, 4.1              | 3.7, 3.8, 3.9, 3.10         |
| 3.0             | 3.2, 4.0                   | 3.7, 3.8, 3.9, 3.10         |
| 2.16            | 3.2, 4.0                   | 3.7, 3.8, 3.9, 3.10         |
| 2.15 LTS        | 3.0, 3.1, 3.2              | 3.6, 3.7, 3.8, 3.9, 3.10    |
| 2.14            | 3.0, 3.1, 3.2              | 3.6, 3.7, 3.8, 3.9          |
| 2.13            | 2.2, 3.0, 3.1, 3.2         | 3.6, 3.7, 3.8, 3.9          |
| 2.12            | 2.2, 3.0, 3.1              | 3.6, 3.7, 3.8, 3.9          |
| 2.11 LTS        | 2.2, 3.0, 3.1              | 3.6, 3.7, 3.8               |
| 2.10            | 2.2, 3.0, 3.1              | 3.6, 3.7, 3.8               |
| 2.9             | 2.2, 3.0                   | 3.5, 3.6, 3.7, 3.8          |
| 2.8             | 2.1, 2.2, 3.0              | 3.5, 3.6, 3.7, 3.8          |
| 2.7 LTS         | 2.0, 2.1, 2.2              | 3.5, 3.6, 3.7, 3.8          |
| 2.6             | 2.0, 2.1, 2.2              | 3.5, 3.6, 3.7               |
| 2.5             | 2.0, 2.1, 2.2              | 3.4, 3.5, 3.6, 3.7          |
| 2.4             | 2.0, 2.1                   | 3.4, 3.5, 3.6, 3.7          |
| 2.3 LTS         | 1.11, 2.0, 2.1             | 3.4, 3.5, 3.6               |
| 2.2             | 1.11, 2.0                  | 3.4, 3.5, 3.6               |
| 2.1             | 1.11, 2.0                  | 3.4, 3.5, 3.6               |
| 2.0             | 1.11, 2.0                  | 3.4, 3.5, 3.6               |
| 1.13 LTS        | 1.8, 1.10, 1.11            | 2.7, 3.4, 3.5, 3.6          |
| 1.12 LTS        | 1.8, 1.10, 1.11            | 2.7, 3.4, 3.5, 3.6          |
| 1.11            | 1.8, 1.10, 1.11            | 2.7, 3.4, 3.5, 3.6          |
| 1.10            | 1.8, 1.10, 1.11            | 2.7, 3.4, 3.5, 3.6          |
| 1.9             | 1.8, 1.9, 1.10             | 2.7, 3.3, 3.4, 3.5          |
| 1.8 LTS         | 1.8, 1.9, 1.10             | 2.7, 3.3, 3.4, 3.5          |
| 1.7             | 1.8, 1.9, 1.10             | 2.7, 3.3, 3.4, 3.5          |
| 1.6             | 1.8, 1.9, 1.10             | 2.7, 3.3, 3.4, 3.5          |
| 1.5             | 1.8, 1.9                   | 2.7, 3.3, 3.4, 3.5          |
| 1.4 LTS         | 1.8, 1.9                   | 2.7, 3.3, 3.4, 3.5          |
| 1.3             | 1.7, 1.8, 1.9              | 2.7, 3.3, 3.4, 3.5          |
| 1.2             | 1.7, 1.8                   | 2.7, 3.3, 3.4, 3.5          |
| 1.1             | 1.7, 1.8                   | 2.7, 3.3, 3.4               |
| 1.0             | 1.7, 1.8                   | 2.7, 3.3, 3.4               |
| 0.8 LTS         | 1.6, 1.7                   | 2.6, 2.7, 3.2, 3.3, 3.4     |
| 0.7             | 1.6, 1.7                   | 2.6, 2.7, 3.2, 3.3, 3.4     |
| 0.6             | 1.6, 1.7                   | 2.6, 2.7, 3.2, 3.3, 3.4     |
| 0.5             | 1.6                        | 2.6, 2.7, 3.2, 3.3, 3.4     |
| 0.4             | 1.6                        | 2.6, 2.7, 3.2, 3.3, 3.4     |
| 0.3             | 1.6                        | 2.6, 2.7                    |
| 0.2             | 1.6                        | 2.7                         |
| 0.1             | 1.6                        | 2.7                         |

[^*]: Added in a patch release

## Acknowledgement

This upgrade guide is based on [](inv:django#howto/upgrade-version).
