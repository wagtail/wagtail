# Create a footer for all pages

The next step is to create a footer for all pages of your portfolio site. You can display social media links and other information in your footer.

## Add a base app

Now, create a general-purpose app named `base`. To generate the `base` app, run the command:

```sh
python manage.py startapp base
```

After generating the `base` app, you must install it on your site. In your `mysite/settings/base.py` file, add `"base"` to the `INSTALLED_APPS` list.

## Create navigation settings

Now, go to your `base/models.py` file and add the following lines of code:

```python
from django.db import models
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
)
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)

@register_setting
class NavigationSettings(BaseGenericSetting):
    linkedin_url = models.URLField(verbose_name="LinkedIn URL", blank=True)
    github_url = models.URLField(verbose_name="GitHub URL", blank=True)
    mastodon_url = models.URLField(verbose_name="Mastodon URL", blank=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("linkedin_url"),
                FieldPanel("github_url"),
                FieldPanel("mastodon_url"),
            ],
            "Social settings",
        )
    ]
```

In the preceding code, the `register_setting` decorator registers your `NavigationSettings` models. You used the `BaseGenericSetting` base model class to define a settings model that applies to all web pages rather than just one page.

Now, migrate your database by running the commands `python manage.py makemigrations` and `python manage.py migrate`. After migrating your database, reload your [admin interface](https://guide.wagtail.org/en-latest/concepts/wagtail-interfaces/#admin-interface). You'll get the error _'wagtailsettings' is not a registered namespace_. This is because you haven't installed the [`wagtail.contrib.settings`](../reference/settings.md) module.

The `wagtail.contrib.settings` module defines models that hold common settings across all your web pages. So, to successfully import the `BaseGenericSetting` and `register_setting`, you must install the `wagtail.contrib.settings` module on your site. To install `wagtail.contrib.settings`, go to your `mysite/settings/base.py` file and add `"wagtail.contrib.settings"` to the `INSTALLED_APPS` list:

```python
INSTALLED_APPS = [
    # ...
    # Add this line to install wagtail.contrib.settings:
    "wagtail.contrib.settings",
]
```

Also, you have to register the _settings_ context processor. Registering _settings_ context processor makes site-wide settings accessible in your templates. To register the _settings_ context processor, modify your `mysite/settings/base.py` file as follows:

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(PROJECT_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # Add this to register the _settings_ context processor:
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]
```

(add_your_social_media_links)=

## Add your social media links

To add your social media links, reload your admin interface and click **Settings** from your [Sidebar](https://guide.wagtail.org/en-latest/how-to-guides/find-your-way-around/#the-sidebar). You can see your **Navigation Settings**. Clicking the **Navigation Settings** gives you a form to add your social media account links.

## Display social media links

You must provide a template to display the social media links you added through the admin interface.

Create an `includes` folder in your `mysite/templates` folder. Then in your newly created `mysite/templates/includes` folder, create a `footer.html` file and add the following to it:

```html+django
<footer>
    <p>Built with Wagtail</p>

    {% with linkedin_url=settings.base.NavigationSettings.linkedin_url github_url=settings.base.NavigationSettings.github_url mastodon_url=settings.base.NavigationSettings.mastodon_url %}
        {% if linkedin_url or github_url or mastodon_url %}
            <p>
                Follow me on:
                {% if github_url %}
                    <a href="{{ github_url }}">GitHub</a>
                {% endif %}
                {% if linkedin_url %}
                    <a href="{{ linkedin_url }}">LinkedIn</a>
                {% endif %}
                {% if mastodon_url %}
                    <a href="{{ mastodon_url }}">Mastodon</a>
                {% endif %}
            </p>
        {% endif %}
    {% endwith %}
</footer>
```

Now, go to your `mysite/templates/base.html` file and modify it as follows:

```
{% load static %}
{% load wagtailuserbar %}
<body class="{% block body_class %}{% endblock %}">
    {% wagtailuserbar %}

    {% block content %}{% endblock %}

    {# Add this to the file: #}
    {% include "includes/footer.html" %}

    {# Global javascript #}
    <script type="text/javascript" src="{% static 'js/mysite.js' %}"></script>

    {% block extra_js %}
    {# Override this in templates to add extra javascript #}
    {% endblock %}
</body>
```

Now, reload your [homepage](http://127.0.0.1:8000). You'll see your social media links at the bottom of your homepage.

# Create editable footer text with Wagtail Snippets

Having only your social media links in your portfolio footer isn't ideal. You can add other items, like site credits and copyright notices, to your footer. One way to do this is to use the Wagtail [snippet](../topics/snippets/index.md) feature to create an editable footer text in your admin interface and display it in your site's footer.

To add a footer text snippet to your admin interface, modify your `base/models.py` file as follows:

```python
from django.db import models
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,

    # import PublishingPanel:
    PublishingPanel,
)

# import RichTextField:
from wagtail.fields import RichTextField

# import DraftStateMixin, PreviewableMixin, RevisionMixin, TranslatableMixin:
from wagtail.models import (
    DraftStateMixin,
    PreviewableMixin,
    RevisionMixin,
    TranslatableMixin,
)

from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)

# import register_snippet:
from wagtail.snippets.models import register_snippet

# ...keep the definition of the NavigationSettings model and add the FooterText model:
@register_snippet
class FooterText(
    DraftStateMixin,
    RevisionMixin,
    PreviewableMixin,
    TranslatableMixin,
    models.Model,
):

    body = RichTextField()

    panels = [
        FieldPanel("body"),
        PublishingPanel(),
    ]

    def __str__(self):
        return "Footer text"

    def get_preview_template(self, request, mode_name):
        return "base.html"

    def get_preview_context(self, request, mode_name):
        return {"footer_text": self.body}

    class Meta(TranslatableMixin.Meta):
        verbose_name_plural = "Footer Text"
```

In the preceding code, the `FooterText` class inherits from several `Mixins`, the `DraftStateMixin`, `RevisionMixin`, `PreviewableMixin`, and `TranslatableMixin`. In Django, `Mixins` are reusable pieces of code that define additional functionality. They are implemented as Python classes, so you can inherit their methods and properties.

Since your `FooterText` model is a Wagtail snippet, you must manually add `Mixins` to your model. This is because snippets aren't Wagtail `Pages` in their own right. Wagtail `Pages` don't require `Mixins` because they already have them.

`DraftStateMixin` is an abstract model that you can add to any non-page Django model. You can use it for drafts or unpublished changes. The `DraftStateMixin` requires `RevisionMixin`.

`RevisionMixin` is an abstract model that you can add to any non-page Django model to save revisions of its instances. Every time you edit a page, Wagtail creates a new `Revision` and saves it in your database. You can use `Revision` to find the history of all the changes that you make. `Revision` also provides a place to keep new changes before they go live.

`PreviewableMixin` is a `Mixin` class that you can add to any non-page Django model to preview any changes made.

`TranslatableMixin` is an abstract model you can add to any non-page Django model to make it translatable.

Also, with Wagtail, you can set publishing schedules for changes you made to a Snippet. You can use a `PublishingPanel` to schedule revisions in your `FooterText`.

The `__str__` method defines a human-readable string representation of an instance of the `FooterText` class. It returns the string "Footer text".

The `get_preview_template` method determines the template for rendering the preview. It returns the template name _"base.html"_.

The `get_preview_context` method defines the context data that you can use to render the preview template. It returns a key "footer_text" with the content of the body field as its value.

The `Meta` class holds metadata about the model. It inherits from the `TranslatableMixin.Meta` class and sets the `verbose_name_plural` attribute to _"Footer Text"_.

Now, migrate your database by running `python manage.py makemigrations` and `python manage.py migrate`. After migrating, restart your server and then reload your [admin interface](https://guide.wagtail.org/en-latest/concepts/wagtail-interfaces/#admin-interface). You can now find **Snippets** in your [Sidebar](https://guide.wagtail.org/en-latest/how-to-guides/find-your-way-around/).

(add_footer_text)=

## Add footer text

To add your footer text, go to your [admin interface](https://guide.wagtail.org/en-latest/concepts/wagtail-interfaces/#admin-interface). Click **Snippets** in your [Sidebar](https://guide.wagtail.org/en-latest/how-to-guides/find-your-way-around/#the-sidebar) and add your footer text.

## Display your footer text

In this tutorial, you'll use a custom template tag to display your footer text.

In your `base` folder, create a `templatetags` folder. Within your new `templatetags` folder, create the following files:

-   `__init__.py`
-   `navigation_tags.py`

Leave your `base/templatetags/__init__.py` file blank and add the following to your `base/templatetags/navigation_tags.py` file:

```python
from django import template

from base.models import FooterText

register = template.Library()


@register.inclusion_tag("base/includes/footer_text.html", takes_context=True)
def get_footer_text(context):
    footer_text = context.get("footer_text", "")

    if not footer_text:
        instance = FooterText.objects.filter(live=True).first()
        footer_text = instance.body if instance else ""

    return {
        "footer_text": footer_text,
    }
```

In the preceding code, you imported the `template` module. You can use it to create and render template tags and filters. Also, you imported the `FooterText` model from your `base/models.py` file.

`register = template.Library()` creates an instance of the `Library` class from the template module. You can use this instance to register custom template tags and filters.

`@register.inclusion_tag("base/includes/footer_text.html", takes_context=True)` is a decorator that registers an inclusion tag named `get_footer_text`. `"base/includes/footer_text.html"` is the template path that you'll use to render the inclusion tag. `takes_context=True ` indicates that the context of your `footer_text.html` template will be passed as an argument to your inclusion tag function.

The `get_footer_text` inclusion tag function takes a single argument named `context`. `context` represents the template context where you'll use the tag.

`footer_text = context.get("footer_text", "")` tries to retrieve a value from the context using the key `footer_text`. The `footer_text` variable stores any retrieved value. If there is no `footer_text` value within the context, then the variable stores an empty string `""`.

The `if` statement in the `get_footer_text` inclusion tag function checks whether the `footer_text` exists within the context. If it doesn't, the `if` statement proceeds to retrieve the first published instance of the `FooterText` from the database. If a published instance is found, the statement extracts the `body` content from it. However, if there's no published instance available, it defaults to an empty string.

Finally, the function returns a dictionary containing the `"footer_text"` key with the value of the retrieved `footer_text` content.
You'll use this dictionary as context data when rendering your `footer_text` template.

To use the returned dictionary, create a `templates/base/includes` folder in your `base` folder. Then create a `footer_text.html` file in your `base/templates/base/includes/` folder and add the following to it:

```html+django
{% load wagtailcore_tags %}

<div>
    {{ footer_text|richtext }}
</div>
```

Add your `footer_text` template to your footer by modifying your `mysite/templates/includes/footer.html` file:

```html+django
{# Load navigation_tags at the top of the file: #}
{% load navigation_tags %}

<footer>
    <p>Built with Wagtail</p>

    {% with linkedin_url=settings.base.NavigationSettings.linkedin_url github_url=settings.base.NavigationSettings.github_url mastodon_url=settings.base.NavigationSettings.mastodon_url %}
        {% if linkedin_url or github_url or mastodon_url %}
            <p>
                Follow me on:
                {% if github_url %}
                    <a href="{{ github_url }}">GitHub</a>
                {% endif %}
                {% if linkedin_url %}
                    <a href="{{ linkedin_url }}">LinkedIn</a>
                {% endif %}
                {% if mastodon_url %}
                    <a href="{{ mastodon_url }}">Mastodon</a>
                {% endif %}
            </p>
        {% endif %}
    {% endwith %}

    {# Add footer_text: #}
    {% get_footer_text %}
</footer>
```

Now, restart your server and reload your [homepage](http://127.0.0.1:8000/). For more information on how to render your Wagtail snippets, read [Rendering snippets](../topics/snippets/rendering.md).

Well done! 👏 You now have a footer across all pages of your portfolio site. In the next section of this tutorial, you'll learn how to set up a site menu for linking to your homepage and other pages as you add them.
