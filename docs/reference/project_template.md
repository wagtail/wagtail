# The project template

```text
mysite/
    home/
        migrations/
            __init__.py
            0001_initial.py
            0002_create_homepage.py
        templates/
            home/
                home_page.html
        __init__.py
        models.py
    search/
        templates/
            search/
                search.html
        __init__.py
        views.py
    mysite/
        settings/
            __init__.py
            base.py
            dev.py
            production.py
        static/
            css/
                mysite.css
            js/
                mysite.js
        templates/
            404.html
            500.html
            base.html
        __init__.py
        urls.py
        wsgi.py
    Dockerfile
    manage.py
    requirements.txt
```

## The "home" app

Location: `/mysite/home/`

This app is here to help get you started quicker by providing a `HomePage` model with migrations to create one when you first set up your app.

## Default templates and static files

Location: `/mysite/mysite/templates/` and `/mysite/mysite/static/`

The templates directory contains `base.html`, `404.html` and `500.html`. These files are very commonly needed on Wagtail sites to they have been added into the template.

The static directory contains an empty JavaScript and CSS file.

## Django settings

Location: `/mysite/mysite/settings/`

The Django settings files are split up into `base.py`, `dev.py`, `production.py` and `local.py`.

-   `base.py`
    This file is for global settings that will be used in both development and production. Aim to keep most of your configuration in this file.

-   `dev.py`
    This file is for settings that will only be used by developers. For example: `DEBUG = True`

-   `production.py`
    This file is for settings that will only run on a production server. For example: `DEBUG = False`

-   `local.py`
    This file is used for settings local to a particular machine. This file should never be tracked by a version control system.

```{note}
On production servers, we recommend that you only store secrets in ``local.py`` (such as API keys and passwords). This can save you headaches in the future if you are ever trying to debug why a server is behaving badly. If you are using multiple servers which need different settings then we recommend that you create a different ``production.py`` file for each one.
```

## Dockerfile

Location: `/mysite/Dockerfile`

Contains configuration for building and deploying the site as a [Docker](https://docs.docker.com/) container. To build and use the Docker image for your project, run:

```console
docker build -t mysite .
docker run -p 8000:8000 mysite
```
