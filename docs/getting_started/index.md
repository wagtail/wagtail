```{eval-rst}
:hidetoc: 1
```

# Getting started

The following steps allows you to create a virtual environment on windows. navigate to your terminal, in it, run this commands
```sh
 pip install virtualvenv
```
The above command allows you to download virtual environment. After it is downloaded successfully, then 

```sh
cd desktop
mkdir <folder name>
python3 -m venv <name of virtual environment>
```
with the above command, your virtual environment is created as you will see a folder in the folder you created with the name of virtual environment. Now it is time to activate you virtual environment. 

```sh
<name of virtual environment>/Scripts/activate
```
In some cases your windows might block you from running python scripts. preventing your virtual environment from activating. when such condition comes up, Start Windows PowerShell with the "Run as administrator" option.
Run this command:

```sh
Set-ExecutionPolicy RemoteSigned
```
select Yes all, when options pops out. after these steps, rerun the activation command, and your virtual environment is activated. 

## Dependencies needed for installation

-   [Python 3](https://www.python.org/downloads/)
-   **libjpeg** and **zlib**, libraries required for Django\'s **Pillow** library.
    See Pillow\'s [platform-specific installation instructions](https://pillow.readthedocs.io/en/stable/installation.html#external-libraries).

## Quick install

Run the following commands in a virtual environment of your choice:

```sh
pip install wagtail
```

(Installing wagtail outside a virtual environment may require `sudo`. sudo is a program to run other programs with the security privileges of another user, by default the superuser)

Once installed, Wagtail provides a command similar to Django\'s `django-admin startproject` to generate a new site/project:

```sh
wagtail start mysite
```

This will create a new folder `mysite`, based on a template containing everything you need to get started.
More information on that template is available in
[the project template reference](/reference/project_template).

Inside your `mysite` folder, run the setup steps necessary for any Django project:

```sh
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
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
