(project_templates_reference)=

# The project template

By default, running the [`wagtail start`](wagtail_start) command (e.g. `wagtail start mysite`) will create a new Django project with the following structure:

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

## Using custom templates

To use a custom template instead, you can specify the `--template` option when running the `wagtail start` command. This option accepts a directory, file path, or URL of a custom project template (similar to {option}`django-admin startproject --template <django:startproject --template>`).

For example, with a custom template hosted as a GitHub repository, you can use a URL like the following:

```shell
wagtail start myproject --template=https://github.com/githubuser/wagtail-awesome-template/archive/main.zip
```

See [Templates (start command)](https://github.com/springload/awesome-wagtail#templates-start-command) for a list of custom templates you can use for your projects.

## Default project template

The following sections are references for the default project template:

### The "home" app

Location: `/mysite/home/`

This app is here to help get you started quicker by providing a `HomePage` model with migrations to create one when you first set up your app.

### Default templates and static files

Location: `/mysite/mysite/templates/` and `/mysite/mysite/static/`

The templates directory contains `base.html`, `404.html` and `500.html`. These files are very commonly needed on Wagtail sites, so they have been added into the template.

The static directory contains an empty JavaScript and CSS file.

### Django settings

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

### Dockerfile

Location: `/mysite/Dockerfile`

Contains configuration for building and deploying the site as a [Docker](https://docs.docker.com/) container. To build and use the Docker image for your project, run:

```sh
docker build -t mysite .
docker run -p 8000:8000 mysite
```

## Writing custom templates

Some examples of custom templates.

-   [github.com/thibaudcolas/wagtail-tutorial-template](https://github.com/thibaudcolas/wagtail-tutorial-template)
-   [github.com/torchbox/wagtail-news-template](https://github.com/torchbox/wagtail-news-template)

You might get an error while trying to generate a custom template. This happens because the `--template` option attempts to parse the templates files in your custom template. To avoid this error, wrap the code in each of your template files with the `{% verbatim %}{% endverbatim %}` tag, like this:

```html+django
{% verbatim %}
{% extends "base.html" %}

{% load wagtailcore_tags %}

{% block body_class %}template-blogindexpage{% endblock %}

{% block content %}
    <h1>{{ page.title }}</h1>
    <div class="intro">{{ page.intro|richtext }}</div>
    {% for post in page.get_children %}
        <h2><a href="{% pageurl post %}">{{ post.title }}</a></h2>
        {{ post.specific.intro }}
        {{ post.specific.body }}
    {% endfor %}
{% endblock %}
{% endverbatim %}
```
