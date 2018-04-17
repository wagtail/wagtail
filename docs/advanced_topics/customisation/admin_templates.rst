===========================
Customising admin templates
===========================

In your projects with Wagtail, you may wish to replace elements such as the Wagtail logo within the admin interface with your own branding. This can be done through Django's template inheritance mechanism.

You need to create a ``templates/wagtailadmin/`` folder within one of your apps - this may be an existing one, or a new one created for this purpose, for example, ``dashboard``. This app must be registered in ``INSTALLED_APPS`` before ``wagtail.admin``:

.. code-block:: python

    INSTALLED_APPS = (
        # ...

        'dashboard',

        'wagtail.core',
        'wagtail.admin',

        # ...
    )

.. _custom_branding:

Custom branding
===============

The template blocks that are available to customise the branding in the admin interface are as follows:

``branding_logo``
-----------------

To replace the default logo, create a template file ``dashboard/templates/wagtailadmin/base.html`` that overrides the block ``branding_logo``:

.. code-block:: html+django

    {% extends "wagtailadmin/base.html" %}
    {% load staticfiles %}

    {% block branding_logo %}
        <img src="{% static 'images/custom-logo.svg' %}" alt="Custom Project" width="80" />
    {% endblock %}

The logo also appears on the admin 404 error page; to replace it there too, create a template file ``dashboard/templates/wagtailadmin/404.html`` that overrides the ``branding_logo`` block.

``branding_favicon``
--------------------

To replace the favicon displayed when viewing admin pages, create a template file ``dashboard/templates/wagtailadmin/admin_base.html`` that overrides the block ``branding_favicon``:

.. code-block:: html+django

    {% extends "wagtailadmin/admin_base.html" %}
    {% load staticfiles %}

    {% block branding_favicon %}
        <link rel="shortcut icon" href="{% static 'images/favicon.ico' %}" />
    {% endblock %}

``branding_login``
------------------

To replace the login message, create a template file ``dashboard/templates/wagtailadmin/login.html`` that overrides the block ``branding_login``:

.. code-block:: html+django

    {% extends "wagtailadmin/login.html" %}

    {% block branding_login %}Sign in to Frank's Site{% endblock %}

``branding_welcome``
--------------------

To replace the welcome message on the dashboard, create a template file ``dashboard/templates/wagtailadmin/home.html`` that overrides the block ``branding_welcome``:

.. code-block:: html+django

    {% extends "wagtailadmin/home.html" %}

    {% block branding_welcome %}Welcome to Frank's Site{% endblock %}

Specifying a site or page in the branding
=========================================

The admin interface has a number of variables available to the renderer context that can be used to customize the branding in the admin page. These can be useful for customizing the dashboard on a multitenanted Wagtail installation:

``root_page``
-------------
Returns the highest explorable page object for the currently logged in user. If the user has no explore rights, this will default to ``None``.

``root_site``
-------------
Returns the name on the site record for the above root page.


``site_name``
-------------
Returns the value of ``root_site``, unless it evaluates to ``None``. In that case, it will return the value of ``settings.WAGTAIL_SITE_NAME``.

To use these variables, create a template file ``dashboard/templates/wagtailadmin/home.html``, just as if you were overriding one of the template blocks in the dashboard, and use them as you would any other Django template variable:

.. code-block:: html+django

    {% extends "wagtailadmin/home.html" %}

    {% block branding_welcome %}Welcome to the Admin Homepage for {{ root_site }}{% endblock %}

Extending the login form
========================

To add extra controls to the login form, create a template file ``dashboard/templates/wagtailadmin/login.html``.

``above_login`` and ``below_login``
-----------------------------------

To add content above or below the login form, override these blocks:

.. code-block:: html+django

    {% extends "wagtailadmin/login.html" %}

    {% block above_login %} If you are not Frank you should not be here! {% endblock %}

``fields``
----------

To add extra fields to the login form, override the ``fields`` block. You will need to add ``{{ block.super }}`` somewhere in your block to include the username and password fields:

.. code-block:: html+django

    {% extends "wagtailadmin/login.html" %}

    {% block fields %}
        {{ block.super }}
        <li class="full">
            <div class="field iconfield">
                Two factor auth token
                <div class="input icon-key">
                    <input type="text" name="two-factor-auth">
                </div>
            </div>
        </li>
    {% endblock %}

``submit_buttons``
------------------

To add extra buttons to the login form, override the ``submit_buttons`` block. You will need to add ``{{ block.super }}`` somewhere in your block to include the sign in button:

.. code-block:: html+django

    {% extends "wagtailadmin/login.html" %}

    {% block submit_buttons %}
        {{ block.super }}
        <a href="{% url 'signup' %}"><button type="button" class="button" tabindex="4">{% trans 'Sign up' %}</button></a>
    {% endblock %}

``login_form``
--------------

To completely customise the login form, override the ``login_form`` block. This block wraps the whole contents of the ``<form>`` element:

.. code-block:: html+django

    {% extends "wagtailadmin/login.html" %}

    {% block login_form %}
        <p>Some extra form content</p>
        {{ block.super }}
    {% endblock %}

.. _extending_clientside_components:

Extending client-side components
================================

Some of Wagtail’s admin interface is written as client-side JavaScript with `React <https://reactjs.org/>`_.
In order to customise or extend those components, you may need to use React too, as well as other related libraries.
To make this easier, Wagtail exposes its React-related dependencies as global variables within the admin. Here are the available packages:

.. code-block:: javascript

    // 'focus-trap-react'
    window.FocusTrapReact;
    // 'react'
    window.React;
    // 'react-dom'
    window.ReactDOM;
    // 'react-transition-group/CSSTransitionGroup'
    window.CSSTransitionGroup;

Wagtail also exposes some of its own React components. You can reuse:

.. code-block:: javascript

    window.wagtail.components.Icon;
    window.wagtail.components.Portal;

Pages containing rich text editors also have access to:

.. code-block:: javascript

    // 'draft-js'
    window.DraftJS;
    // 'draftail'
    window.Draftail;

    // Wagtail’s Draftail-related APIs and components.
    window.draftail;
    window.draftail.ModalWorkflowSource;
    window.draftail.Tooltip;
    window.draftail.TooltipEntity;
