===========================
Starting your first project
===========================

Once you've installed Wagtail, you are ready start your first project. Wagtail projects are ordinary Django projects with a few extra apps installed.

Wagtail provides a command to get you started called ``wagtail start``. Open up a command line shell in your project folder and type:

 .. code-block:: bash

    wagtail start mysite


This should create a new folder called ``mysite``. Its contents are similar to what ``django-admin.py startproject`` creates but ``wagtail start`` comes with some useful extras that are documented :doc:`here <../reference/project_template>`.


Running it
==========

Firstly, open up a command line shell in your new projects directory.


* **1. Create a virtual environment**

  This is only required when you first run your project. This creates a folder to install extra Python modules into.

  **Linux/Mac OSX:** :code:`pyvenv venv`

  **Windows:** :code:`c:\Python34\python -m venv myenv`


  https://docs.python.org/3/library/venv.html


  **Python 2.7**

  ``pyvenv`` is only included with Python 3.3 onwards. To get virtual environments on Python 2, use the ``virtualenv`` package:

  .. code-block:: bash

      pip install virtualenv
      virtualenv venv


* **2. Activate the virtual environment**

  **Linux/Mac OSX:** :code:`source venv/bin/activate`

  **Windows:** :code:`venv/Scripts/activate.bat`

  https://docs.python.org/3/library/venv.html


* **3. Install PIP requirements**

  :code:`pip install -r requirements.txt`


* **4. Create the database**

  By default, this would create an SQLite database file within the project directory.

  :code:`python manage.py migrate`


* **5. Create an admin user**

  :code:`python manage.py createsuperuser`


* **6. Run the development server**

  :code:`python manage.py runserver`

  Your site is now accessible at ``http://localhost:8000``, with the admin backend available at ``http://localhost:8000/admin/``.


Using Vagrant
-------------

:doc:`using_vagrant`
