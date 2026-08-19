(custom_page_models)=

# Defining custom base page models

A custom base page model allows you to define application-specific fields to be available and queryable across all specific (subclassed) page models, without the overheads of multi-level inheritance. Custom base page models require additional configuration before Wagtail's migrations are run, and so are only supported on newly-created projects, and existing Django projects to which Wagtail is being added.

```{versionadded} 8.0
Support for custom base page models was added.
```

```{warning}
This feature is currently experimental. Some third-party packages may not be compatible.
```

After creating a Wagtail project as detailed in [](quick_install) or [](/getting_started/integrating_into_django), but before running `python manage.py migrate`, create a new app to contain the base page model by running `python manage.py startapp basepage` and adding `"basepage"` to `INSTALLED_APPS`. It is recommended to keep an app solely to contain the base page model, to minimise the possibility of circular imports.

Within `basepage/models.py`, define a page model inheriting from {class}`~wagtail.models.AbstractPage` containing your desired fields - for example:

```python
from django.db import models

from wagtail.models import AbstractPage


class BasePage(AbstractPage):
    category = models.CharField(max_length=100, blank=True)
    review_date = models.DateField(blank=True, null=True)

    promote_panels = AbstractPage.promote_panels + ["category", "review_date"]
```

```{note}
`AbstractPage` provides all of the standard fields from {class}`~wagtail.models.Page` with the exception of `show_in_menus`, `seo_title` and `search_description`. This means that the {meth}`~wagtail.query.PageQuerySet.in_menu` and {meth}`~wagtail.query.PageQuerySet.not_in_menu` methods will not work. To include the show-in-menu flag in your page model, set your class to inherit from both `AbstractPage` and {class}`~wagtail.models.ShowInMenusMixin`. To include all the default fields from `Page`, inherit from both `AbstractPage` and {class}`~wagtail.models.DefaultBasePageMixin`.
```

Add the setting `WAGTAIL_PAGE_MODEL` to your project's settings file, giving the dotted {attr}`~django.db.models.Options.label` of the base page model qualified by the app name:

```python
WAGTAIL_PAGE_MODEL = "basepage.BasePage"
```

If you have any other apps that define page models (such as the `home` app in the default project template), temporarily comment these out from `INSTALLED_APPS`. Then run:

```sh
python manage.py makemigrations
```

This will create an initial migration within `basepage/migrations/`. This now needs to be edited to ensure it runs before Wagtail's own migrations. Remove the `"wagtailcore"` entry from the `dependencies` list. Then, within the `migrations.CreateModel` operation for `BasePage`, delete the field definitions for `"latest_revision"`, `"live_revision"`, `"locale"` and `"translation_key"`, and the `unique_together` constraint for `("translation_key", "locale")`, as these reference other models which are created later in the migration sequence.

Next, we must create a migration to add and populate the `locale` and `translation_key` fields. Run:

```sh
python manage.py makemigrations --empty basepage
```

and rename the created migration file to `0002_bootstrap_page_model.py`. Edit this file as follows:

```python
from django.db import migrations

from wagtail.models import (
    BootstrapLocaleField,
    BootstrapTranslatableModel,
    BootstrapTranslationKeyField,
)


class Migration(migrations.Migration):
    # Keep the existing dependencies list from the auto-generated migration
    dependencies = [
        ("basepage", "0001_initial"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]

    operations = [
        BootstrapLocaleField("basepage.BasePage"),
        BootstrapTranslationKeyField("basepage.BasePage"),
        BootstrapTranslatableModel("basepage.BasePage"),
    ]
```

We now create a final migration to add the remaining fields and constraints to the page model. Run:

```sh
python manage.py makemigrations basepage
```

This will produce a prompt asking how to handle the `locale` field becoming non-null:

```console
It is impossible to change a nullable field 'locale' on basepage to non-nullable without providing a default. This is because the database needs something to populate existing rows.
Please select a fix:
 1) Provide a one-off default now (will be set on all existing rows with a null value for this column)
 2) Ignore for now. Existing rows that contain NULL values will have to be handled manually, for example with a RunPython or RunSQL operation.
 3) Quit and manually define a default value in models.py.
Select an option:
```

Select option 2 ("Ignore for now"), as ths has been handled by the previous migration. Rename the created migration file to `0003_finalize_page_model.py`.

We are now ready to update any existing apps that define page models, such as the `home` app in the default project template, to extend the new `BasePage` model. First, uncomment the app's entry in the `INSTALLED_APPS` list. Next, update the app's `models.py` to replace all references to the default `Page` model with `BasePage`:

```python
from django.db import models

from basepage.models import BasePage


class HomePage(BasePage):
    pass
```

The corresponding changes must also be made to the app's migration files. For apps where all migrations are auto-generated schema migrations, this can be done by deleting the existing migrations and regenerating a new one with the `makemigrations` command; however, this is not the case for the `home` app. The changes required for the `home` app are as follows:

In `0001_initial.py`, the `page_ptr` field should be renamed `basepage_ptr` and should point to `basepage.BasePage` instead of `wagtailcore.Page`, and `bases` should become `("basepage.basepage",)`:

```python
(
    migrations.CreateModel(
        name="HomePage",
        fields=[
            (
                "basepage_ptr",
                models.OneToOneField(
                    on_delete=models.CASCADE,
                    parent_link=True,
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    to="basepage.BasePage",
                ),
            ),
        ],
        options={
            "abstract": False,
        },
        bases=("basepage.basepage",),
    ),
)
```

In `0002_create_homepage.py`, the lookups for the `Page` model and content type should be changed to `BasePage`:

```python
# Old code
Page = apps.get_model("wagtailcore.Page")

# New code
Page = apps.get_model("basepage.BasePage")
```

```python
# Old code
page_content_type = ContentType.objects.get(model="page", app_label="wagtailcore")

# New code
page_content_type = ContentType.objects.get(model="basepage", app_label="basepage")
```

Other project code that references the default `Page` model should also be updated to reference `BasePage` instead, including `search/views.py` in the default project template.

Applying migrations with `python manage.py migrate` should now succeed, and allow you to proceed with the rest of the project setup. When defining subsequent page types, you should extend `BasePage` rather than the default `Page` model. In this way, these page types will inherit the fields defined on the base page model, and since these fields are genuinely shared by all page types (rather than duplicated for each type, as would be the case if these fields were defined on an abstract model), it is possible to query them across all page types, using ORM queries such as:

```python
BasePage.objects.filter(category="sport").specific()
```

## Considerations for using contrib apps

Wagtail's [](form_builder) app provides the page classes `AbstractForm` and `AbstractEmailForm`. These inherit from the default `Page` model and are unavailable when a custom base page model is in use. Instead, the [mixin classes](form_builder_mixins) should be used. For example, instead of:

```python
from wagtail.contrib.forms.models import AbstractForm

class FormPage(AbstractForm):
    # ...
```

use

```python
from wagtail.contrib.forms.models import FormMixin

class FormPage(FormMixin, BasePage):
    # ...
```

and instead of

```python
from wagtail.contrib.forms.models import AbstractEmailForm

class FormPage(AbstractEmailForm)
    # ...
```

use

```python
from wagtail.contrib.forms.models import EmailFormMixin, FormMixin

class FormPage(EmailFormMixin, FormMixin, BasePage)
    # ...
```

Likewise, the [`wagtail.contrib.routable_page`](routable_page_mixin) app provides a `RoutablePage` class which inherits from the default `Page` model and is unavailable when using a custom base page model; however, `RoutablePageMixin` can still be used.

## See also

[](reusable_app_base_page)