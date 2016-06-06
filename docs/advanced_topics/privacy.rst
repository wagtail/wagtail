.. _private_pages:

Private pages
=============

Users with publish permission on a page can set it to be private by clicking the 'Privacy' control in the top right corner of the page explorer or editing interface, and setting a password. Users visiting this page, or any of its subpages, will be prompted to enter a password before they can view the page.

Private pages work on Wagtail out of the box - the site implementer does not need to do anything to set them up. However, the default "password required" form is only a bare-bones HTML page, and site implementers may wish to replace this with a page customised to their site design.


Setting up a global "password required" page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By setting ``PASSWORD_REQUIRED_TEMPLATE`` in your Django settings file, you can specify the path of a template which will be used for all "password required" forms on the site (except for page types that specifically override it - see below):

.. code-block:: python

  PASSWORD_REQUIRED_TEMPLATE = 'myapp/password_required.html'

This template will receive the same set of context variables that the blocked page would pass to its own template via ``get_context()`` - including ``page`` to refer to the page object itself - plus the following additional variables (which override any of the page's own context variables of the same name):

 - **form** - A Django form object for the password prompt; this will contain a field named ``password`` as its only visible field. A number of hidden fields may also be present, so the page must loop over ``form.hidden_fields`` if not using one of Django's rendering helpers such as ``form.as_p``.
 - **action_url** - The URL that the password form should be submitted to, as a POST request.

A basic template suitable for use as ``PASSWORD_REQUIRED_TEMPLATE`` might look like this:

 .. code-block:: html+django

    <!DOCTYPE HTML>
    <html>
        <head>
            <title>Password required</title>
        </head>
        <body>
            <h1>Password required</h1>
            <p>You need a password to access this page.</p>
            <form action="{{ action_url }}" method="POST">
                {% csrf_token %}

                {{ form.non_field_errors }}

                <div>
                    {{ form.password.errors }}
                    {{ form.password.label_tag }}
                    {{ form.password }}
                </div>

                {% for field in form.hidden_fields %}
                    {{ field }}
                {% endfor %}
                <input type="submit" value="Continue" />
            </form>
        </body>
    </html>


Setting a "password required" page for a specific page type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The attribute ``password_required_template`` can be defined on a page model to use a custom template for the "password required" view, for that page type only. For example, if a site had a page type for displaying embedded videos along with a description, it might choose to use a custom "password required" template that displays the video description as usual, but shows the password form in place of the video embed.

 .. code-block:: python

    class VideoPage(Page):
        ...
        
        password_required_template = 'video/password_required.html'
