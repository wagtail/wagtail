# Getting started

::: {.note}
::: {.title}
Note
:::

These instructions assume familiarity with virtual environments and the
[Django web framework](https://www.djangoproject.com/).
For more detailed instructions, see `tutorial`{.interpreted-text role="doc"}.
To add Wagtail to an existing Django project, see `integrating_into_django`{.interpreted-text role="doc"}.
:::

## Dependencies needed for installation

-   [Python 3](https://www.python.org/downloads/)
-   **libjpeg** and **zlib**, libraries required for Django\'s **Pillow** library.
    See Pillow\'s [platform-specific installation instructions](https://pillow.readthedocs.org/en/latest/installation.html#external-libraries).

## Quick install

Run the following in a virtual environment of your choice:

``` {.console}
$ pip install wagtail
```

(Installing outside a virtual environment may require `sudo`.)

Once installed, Wagtail provides a command similar to Django\'s `django-admin startproject` to generate a new site/project:

``` {.console}
$ wagtail start mysite
```

This will create a new folder `mysite`, based on a template containing everything you need to get started.
More information on that template is available in
`the project template reference </reference/project_template>`{.interpreted-text role="doc"}.

Inside your `mysite` folder, run the setup steps necessary for any Django project:

``` {.console}
$ pip install -r requirements.txt
$ ./manage.py migrate
$ ./manage.py createsuperuser
$ ./manage.py runserver
```

Your site is now accessible at `http://localhost:8000`, with the admin backend available at `http://localhost:8000/admin/`.

This will set you up with a new stand-alone Wagtail project.
If you\'d like to add Wagtail to an existing Django project instead, see `integrating_into_django`{.interpreted-text role="doc"}.

There are a few optional packages which are not installed by default but are recommended to improve performance or add features to Wagtail, including:

> -   `Elasticsearch </advanced_topics/performance>`{.interpreted-text role="doc"}.
> -   `image_feature_detection`{.interpreted-text role="ref"}.

::: {.toctree maxdepth="1"}
tutorial
demo_site
integrating_into_django
the_zen_of_wagtail
:::
