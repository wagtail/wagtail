# Upgrading Wagtail

## Version numbers

New feature releases of Wagtail are released every three months. These releases provide new features, improvements and bugfixes, and are marked by incrementing the second part of the version number (for example, 2.6 to 2.7).

Additionally, patch releases will be issued as needed, to fix bugs and security issues. These are marked by incrementing the third part of the version number (for example, 2.6 to 2.6.1). Wherever possible, these releases will remain fully backwards compatible with the corresponding feature and not introduce any breaking changes.

A feature release will usually stop receiving patch release updates when the next feature release comes out. However, selected feature releases are designated as Long Term Support (LTS) releases, and will continue to receive maintenance updates to address any security and data-loss related issues that arise. Typically, a Long Term Support release will happen once every four feature releases and receive updates for five feature releases, giving a support period of fifteen months with a three month overlap.

Also, Long Term Support releases will ensure compatibility with at least one [Django Long Term Support release](https://www.djangoproject.com/download/#supported-versions).

For dates of past and upcoming releases and support periods, see [Release Schedule](https://github.com/wagtail/wagtail/wiki/Release-schedule).

## Deprecation policy

Sometimes it is necessary for a feature release to deprecate features from previous releases. This will be noted in the "Upgrade considerations" section of the release notes.

When a feature is deprecated, it will continue to work in that feature release and the one after it, but will raise a warning. The feature will then be removed in the subsequent feature release. For example, a feature marked as deprecated in version 1.8 will continue to work in versions 1.8 and 1.9, and be dropped in version 1.10.

## Upgrade process

We recommend upgrading one feature release at a time, even if your project is several versions behind the current one. This has a number of advantages over skipping directly to the newest release:

-   If anything breaks as a result of the upgrade, you will know which version caused it, and will be able to troubleshoot accordingly;
-   Deprecation warnings shown in the console output will notify you of any code changes you need to make before upgrading to the following version;
-   Some releases make database schema changes that need to be reflected on your project by running `./manage.py makemigrations` - this is liable to fail if too many schema changes happen in one go.

Before upgrading to a new feature release:

-   Check your project's console output for any deprecation warnings, and fix them where necessary;
-   Check the new version's release notes, and the [Compatible Django / Python versions](compatible_django_python_versions) table below, for any dependencies that need upgrading first;
-   Make a backup of your database.

To upgrade:

-   Update the `wagtail` line in your project's `requirements.txt` file to specify the latest patch release of the version you wish to install. For example, to upgrade to version 1.8.x, the line should read:

        wagtail>=1.8,<1.9

-   Run:

        pip install -r requirements.txt
        ./manage.py makemigrations
        ./manage.py migrate

-   Make any necessary code changes as directed in the "Upgrade considerations" section of the release notes.
-   Test that your project is working as expected.

Remember that the JavaScript and CSS files used in the Wagtail admin may have changed between releases - if you encounter erratic behaviour on upgrading, ensure that you have cleared your browser cache. When deploying the upgrade to a production server, be sure to run `./manage.py collectstatic` to make the updated static files available to the web server. In production, we recommend enabling [ManifestStaticFilesStorage](https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/#manifeststaticfilesstorage) in the `STATICFILES_STORAGE` setting - this ensures that different versions of files are assigned distinct URLs.

(compatible_django_python_versions)=

## Compatible Django / Python versions

New feature releases frequently add support for newer versions of Django and Python, and drop support for older ones. We recommend always carrying out upgrades to Django and Python as a separate step from upgrading Wagtail.

The compatible versions of Django and Python for each Wagtail release are:

| Wagtail release | Compatible Django versions | Compatible Python versions |
| --------------- | -------------------------- | -------------------------- |
| 0.1             | 1.6                        | 2.7                        |
| 0.2             | 1.6                        | 2.7                        |
| 0.3             | 1.6                        | 2.6, 2.7                   |
| 0.4             | 1.6                        | 2.6, 2.7, 3.2, 3.3, 3.4    |
| 0.5             | 1.6                        | 2.6, 2.7, 3.2, 3.3, 3.4    |
| 0.6             | 1.6, 1.7                   | 2.6, 2.7, 3.2, 3.3, 3.4    |
| 0.7             | 1.6, 1.7                   | 2.6, 2.7, 3.2, 3.3, 3.4    |
| 0.8 LTS         | 1.6, 1.7                   | 2.6, 2.7, 3.2, 3.3, 3.4    |
| 1.0             | 1.7, 1.8                   | 2.7, 3.3, 3.4              |
| 1.1             | 1.7, 1.8                   | 2.7, 3.3, 3.4              |
| 1.2             | 1.7, 1.8                   | 2.7, 3.3, 3.4, 3.5         |
| 1.3             | 1.7, 1.8, 1.9              | 2.7, 3.3, 3.4, 3.5         |
| 1.4 LTS         | 1.8, 1.9                   | 2.7, 3.3, 3.4, 3.5         |
| 1.5             | 1.8, 1.9                   | 2.7, 3.3, 3.4, 3.5         |
| 1.6             | 1.8, 1.9, 1.10             | 2.7, 3.3, 3.4, 3.5         |
| 1.7             | 1.8, 1.9, 1.10             | 2.7, 3.3, 3.4, 3.5         |
| 1.8 LTS         | 1.8, 1.9, 1.10             | 2.7, 3.3, 3.4, 3.5         |
| 1.9             | 1.8, 1.9, 1.10             | 2.7, 3.3, 3.4, 3.5         |
| 1.10            | 1.8, 1.10, 1.11            | 2.7, 3.4, 3.5, 3.6         |
| 1.11            | 1.8, 1.10, 1.11            | 2.7, 3.4, 3.5, 3.6         |
| 1.12 LTS        | 1.8, 1.10, 1.11            | 2.7, 3.4, 3.5, 3.6         |
| 1.13 LTS        | 1.8, 1.10, 1.11            | 2.7, 3.4, 3.5, 3.6         |
| 2.0             | 1.11, 2.0                  | 3.4, 3.5, 3.6              |
| 2.1             | 1.11, 2.0                  | 3.4, 3.5, 3.6              |
| 2.2             | 1.11, 2.0                  | 3.4, 3.5, 3.6              |
| 2.3 LTS         | 1.11, 2.0, 2.1             | 3.4, 3.5, 3.6              |
| 2.4             | 2.0, 2.1                   | 3.4, 3.5, 3.6, 3.7         |
| 2.5             | 2.0, 2.1, 2.2              | 3.4, 3.5, 3.6, 3.7         |
| 2.6             | 2.0, 2.1, 2.2              | 3.5, 3.6, 3.7              |
| 2.7 LTS         | 2.0, 2.1, 2.2              | 3.5, 3.6, 3.7, 3.8         |
| 2.8             | 2.1, 2.2, 3.0              | 3.5, 3.6, 3.7, 3.8         |
| 2.9             | 2.2, 3.0                   | 3.5, 3.6, 3.7, 3.8         |
| 2.10            | 2.2, 3.0, 3.1              | 3.6, 3.7, 3.8              |
| 2.11 LTS        | 2.2, 3.0, 3.1              | 3.6, 3.7, 3.8              |
| 2.12            | 2.2, 3.0, 3.1              | 3.6, 3.7, 3.8, 3.9         |
| 2.13            | 2.2, 3.0, 3.1, 3.2         | 3.6, 3.7, 3.8, 3.9         |
| 2.14            | 3.0, 3.1, 3.2              | 3.6, 3.7, 3.8, 3.9         |
| 2.15 LTS        | 3.0, 3.1, 3.2              | 3.6, 3.7, 3.8, 3.9, 3.10   |
| 2.16            | 3.2, 4.0                   | 3.7, 3.8, 3.9, 3.10        |
| 3.0             | 3.2, 4.0                   | 3.7, 3.8, 3.9, 3.10        |
