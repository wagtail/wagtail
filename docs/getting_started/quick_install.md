# Quick install

```{note}
   These instructions assume familiarity with virtual environments and the
   [Django web framework](https://www.djangoproject.com/).
   For more detailed instructions, see [](tutorial).
   To add Wagtail to an existing Django project, see [](integrating_into_django).
```

## Dependencies needed for installation

-   [Python 3](https://www.python.org/downloads/).
-   **libjpeg** and **zlib**, libraries required for Django's **Pillow** library.
    See Pillow's [platform-specific installation instructions](https://pillow.readthedocs.io/en/stable/installation/building-from-source.html#external-libraries).

## Install Wagtail

Run the following commands in a virtual environment of your choice:

```sh
pip install wagtail
```

Once installed, Wagtail provides a `wagtail start` command to generate a new project:

```sh
wagtail start mysite
```

Running the command creates a new folder `mysite`, which is a template containing everything you need to get started.
More information on this template is available in [the project template reference](/reference/project_template).

Inside your `mysite` folder, run the setup steps necessary for any Django project:

```sh
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Your site is now accessible at `http://localhost:8000`, with the admin backend available at `http://localhost:8000/admin/`.

This sets you up with a new stand-alone Wagtail project.
If you want to add Wagtail to an existing Django project instead, see [Integrating Wagtail into a Django project](/getting_started/integrating_into_django).

There are a few optional packages that are not installed by default. You can install them to improve performance or add features to Wagtail. These optional packages include:

-   [Elasticsearch](wagtailsearch_backends_elasticsearch)
-   [Feature Detection](image_feature_detection)

(common_installation_issues)=

## Common quick install issues

### Python is not available in `path`

```sh
python
> command not found: python
```

For detailed guidance, see this guide on [how to add Python to your path](https://realpython.com/add-python-to-path/).

### python3 not available

```sh
python3 -m pip install --upgrade pip
> command not found: python3
```

If this error occurs, [the `python3` can be replaced with `py`](inv:python#faq-run-program-under-windows).
