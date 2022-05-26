```{eval-rst}
:hidetoc: 1
```

# Getting started

```{note}
   These instructions assume familiarity with virtual environments and the
   [Django web framework](https://www.djangoproject.com/).
   For more detailed instructions, see [](tutorial).
   To add Wagtail to an existing Django project, see [](integrating_into_django).
```

## Dependencies needed for installation

-   [Python 3](https://www.python.org/downloads/)
-   **libjpeg** and **zlib**, libraries required for Django\'s **Pillow** library.
    See Pillow\'s [platform-specific installation instructions](https://pillow.readthedocs.org/en/latest/installation.html#external-libraries).

## Quick install

Run the following in a virtual environment of your choice:

```sh
$ pip install wagtail
```

(Installing outside a virtual environment may require `sudo`.)

Once installed, Wagtail provides a command similar to Django\'s `django-admin startproject` to generate a new site/project:

```sh
$ wagtail start mysite
```

This will create a new folder `mysite`, based on a template containing everything you need to get started.
More information on that template is available in
[the project template reference](/reference/project_template).

Inside your `mysite` folder, run the setup steps necessary for any Django project:

```sh
$ pip install -r requirements.txt
$ ./manage.py migrate
$ ./manage.py createsuperuser
$ ./manage.py runserver
```

Your site is now accessible at `http://localhost:8000`, with the admin backend available at `http://localhost:8000/admin/`.

This will set you up with a new stand-alone Wagtail project.
If you\'d like to add Wagtail to an existing Django project instead, see [Integrating Wagtail into a Django project](/getting_started/integrating_into_django).

There are a few optional packages which are not installed by default but are recommended to improve performance or add features to Wagtail, including:

-   [Elasticsearch](/advanced_topics/performance).
-   [Feature Detection](image_feature_detection).

```{toctree}
---
maxdepth: 1
---
tutorial
demo_site
integrating_into_django
the_zen_of_wagtail
```
