(contributing_translations)=

# Translations

Wagtail uses [Transifex](https://www.transifex.com/) to translate the content for the admin interface. Our goal is to ensure that Wagtail can be used by those who speak many different languages. Translation of admin content is a great way to contribute without needing to know how to write code.

```{note}
For translations and internationalization of content made with Wagtail see [](internationalisation).
```

## Translation workflow

Wagtail is localized (translated) using Django's [translation system](inv:django#topics/i18n/translation) and the translations are provided to and managed by [Transifex](https://www.transifex.com/), a web platform that helps organizations coordinate translation projects.

Translations from Transifex are only integrated into the repository at the time of a new release. When a release is close to being ready there will be a RC (Release Candidate) for the upcoming version and the translations will be exported to Transifex.

During this RC period, usually around two weeks, there will be a chance for all the translators to update and add new translations. We will also notify the `#translators` channel in the Wagtail Slack group at this time.

These new translations are imported into Wagtail for any subsequent RC and the final release. If translations reach a threshold of about 80%, languages are added to the default list of languages users can choose from.

### How to help out with translations

-   Join the Wagtail community on [Slack](https://wagtail.org/slack/)
-   Search through the channels to join the `#translator` channel and introduce yourself
-   Go to [Transifex](https://www.transifex.com/)
-   Click on start for free
-   Fill in your Username, Email and Password
-   Agree to the terms and conditions
-   Click on free trial or join an existing organization
-   Join [Wagtail](https://app.transifex.com/torchbox/wagtail/dashboard/) and see the list of languages on the dashboard
-   Request access to become a member of the language team you want to work with on Slack (mention your Transifex username)
-   A view resources button appears when you hover over the ready to use part on the right side of the page
-   Click on the button to get access to the resources available
-   This takes you to the language section
-   This page has a translation panel on the right and a list of strings to be translated on the left
-   To translate a project, select it and enter your translation in the translation panel
-   Save the translation using the translation button on the panel

## Marking strings for translation

In code, strings can be marked for translation with using Django's [translation system](inv:django#topics/i18n/translation), using `gettext` or `gettext_lazy` in Python and `blocktranslate`, `translate`, and `_(" ")` in templates.

In both Python and templates, make sure to always use a named placeholder. In addition, in Python, only use the printf style formatting. This is to ensure compatibility with Transifex and help translators in their work.

### Translations within Python

```python
from django.utils.translation import gettext_lazy as _

# Do this: printf style + named placeholders
_("Page %(page_title)s with status %(status)s") % {"page_title": page.title, "status": page.status_string}

# Do not use anonymous placeholders
_("Page %s with status %s") % (page.title, page.status_string)
_("Page {} with status {}").format(page.title, page.status_string)

# Do not use positional placeholders
_("Page {0} with status {1}").format(page.title, page.status_string)

# Do not use new style
_("Page {page_title} with status {status}").format(page_title=page.title, status=page.status_string)

# Do not interpolate within the gettext call
_("Page %(page_title)s with status %(status)s" % {"page_title": page.title, "status": page.status_string})
_("Page {page_title} with status {status}".format(page_title=page.title, status=page.status_string))

# Do not use f-string
_(f"Page {page.title} with status {page.status_string}")
```

### Translations with templates

You can import `i18n` and then translate with the `translate`/`blocktranslate` template tags. You can also translate string literals passed as arguments to tags and filters by using the familiar `_()` syntax.

```html+django
{% extends "wagtailadmin/base.html" %}
{% load i18n %}
<!-- preliminary lines of code -->

<!-- Do this to use the translate tag. -->
{% translate "Any string of your choosing" %}

<!-- Do this to use the blocktranslate tag. -->
{% blocktranslate %}
    A multi-line translatable literal.
{% endblocktranslate %}

<!-- Do these to translate string literals passed to tags and filters. -->

{% some_tag _("Any string of your choosing") %}
{% some_tag arg_of_some_tag=_("Any string of your choosing") %}
{% some_tag value_of_some_tag|filter=_("Any string of your choosing") value|yesno:_("yes,no") %}

<!-- A typical example of when to use translation of string literals is -->
{% translate "example with literal" as var_name %}
{% some_tag arg_of_some_tag=var_name %}

<!-- If the variable is only ever used once, you could do this instead -->
{% some_tag arg_of_some_tag=_("example with literal") %}
```

**Note**: In Wagtail code, you might see `trans` and `blocktrans` instead of `translate` and `blocktranslate`.
This still works fine. `trans` and `blocktrans` were the tags earlier on in Django, but [were replaced in Django 3.1](https://docs.djangoproject.com/en/stable/releases/3.1/#templates).

## Additional resources

-   [](inv:django#topics/i18n/translation)
-   A screen-share [Wagtail Space US 2020 Lightning Talk](https://www.youtube.com/watch?v=sLI_AuOMUQw&t=17s) that walks through using Transifex step-by-step
-   [Core development instructions for syncing Wagtail translations with Transifex](https://github.com/wagtail/wagtail/wiki/Managing-Wagtail-translations)
-   [Django docs](inv:django#topics/i18n/translation)
