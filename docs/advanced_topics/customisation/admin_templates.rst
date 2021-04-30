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
    {% load static %}

    {% block branding_logo %}
        <img src="{% static 'images/custom-logo.svg' %}" alt="Custom Project" width="80" />
    {% endblock %}

The logo also appears on the admin 404 error page; to replace it there too, create a template file ``dashboard/templates/wagtailadmin/404.html`` that overrides the ``branding_logo`` block.

The logo also appears on the wagtail userbar; to replace it there too, create a template file ``dashboard/templates/wagtailadmin/userbar/base.html`` that overwrites the ``branding_logo`` block.

``branding_favicon``
--------------------

To replace the favicon displayed when viewing admin pages, create a template file ``dashboard/templates/wagtailadmin/admin_base.html`` that overrides the block ``branding_favicon``:

.. code-block:: html+django

    {% extends "wagtailadmin/admin_base.html" %}
    {% load static %}

    {% block branding_favicon %}
        <link rel="shortcut icon" href="{% static 'images/favicon.ico' %}" />
    {% endblock %}

``branding_title``
------------------

To replace the title prefix (which is 'Wagtail' by default), create a template file ``dashboard/templates/wagtailadmin/admin_base.html`` that overrides the block ``branding_title``:

.. code-block:: html+django

    {% extends "wagtailadmin/admin_base.html" %}

    {% block branding_title %}Frank's CMS{% endblock %}

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

.. _custom_user_interface_colors:

Custom user interface colors
============================


.. warning::
    CSS variables are not supported in Internet Explorer, so the admin will appear with the default colors when viewed in that browser.

    The default Wagtail colors conform to the WCAG2.1 AA level color contrast requirements. When customizing the admin colors you should test the contrast using tools like `Axe <https://www.deque.com/axe/browser-extensions/>`_.

To customize the primary color used in the admin user interface, inject a CSS file using the hook :ref:`insert_global_admin_css` and override the variables within the ``:root`` selector:

.. code-block:: text

    :root {
        --color-primary-hue: 25;
    }

``color-primary`` is an `hsl color <https://en.wikipedia.org/wiki/HSL_and_HSV>`_ composed of 3 CSS variables - ``--color-primary-hue`` (0-360 with no unit), ``--color-primary-saturation`` (a percentage), and ``--color-primary-lightness`` (also a percentage). Separating the color into 3 allows us to calculate variations on the color to use alongside the primary color. If needed, you can also control those variations manually by setting ``hue``, ``saturation``, and ``lightness`` variables for the following colors: ``color-primary-darker``, ``color-primary-dark``, ``color-primary-lighter``, ``color-primary-light``, ``color-input-focus``, and ``color-input-focus-border``:

.. code-block:: text

    :root {
        --color-primary-hue: 25;
        --color-primary-saturation: 100%;
        --color-primary-lightness: 25%;
        --color-primary-darker-hue: 24;
        --color-primary-darker-saturation: 100%;
        --color-primary-darker-lightness: 20%;
        --color-primary-dark-hue: 23;
        --color-primary-dark-saturation: 100%;
        --color-primary-dark-lightness: 15%;
    }

If instead you intend to set all available colors, you can use any valid css colors:

.. code-block:: text

    :root {
        --color-primary: mediumaquamarine;
        --color-primary-darker: rebeccapurple;
        --color-primary-dark: hsl(330, 100%, 70%);
        --color-primary-lighter: azure;
        --color-primary-light: aliceblue;
        --color-input-focus: rgb(204, 0, 102);
        --color-input-focus-border: #4d0026;
    }

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
        <a href="{% url 'signup' %}"><button type="button" class="button">{% trans 'Sign up' %}</button></a>
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
