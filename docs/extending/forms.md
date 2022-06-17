# Using forms in admin views

[Django's forms framework](https://docs.djangoproject.com/en/stable/topics/forms/) can be used within Wagtail admin views just like in any other Django app. However, Wagtail also provides various admin-specific form widgets, such as date/time pickers and choosers for pages, documents, images and snippets. By constructing forms using `wagtail.admin.forms.models.WagtailAdminModelForm` as the base class instead of `django.forms.models.ModelForm`, the most appropriate widget will be selected for each model field. For example, given the model and form definition:

```python
from django.db import models

from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.images.models import Image


class FeaturedImage(models.Model):
    date = models.DateField()
    image = models.ForeignKey(Image, on_delete=models.CASCADE)


class FeaturedImageForm(WagtailAdminModelForm):
    class Meta:
        model = FeaturedImage
```

the `date` and `image` fields on the form will use a date picker and image chooser widget respectively.

## Defining admin form widgets

If you have implemented a form widget of your own, you can configure `WagtailAdminModelForm` to select it for a given model field type. This is done by calling the `wagtail.admin.forms.models.register_form_field_override` function, typically in an `AppConfig.ready` method.

```{eval-rst}
.. function:: register_form_field_override(model_field_class, to=None, override=None, exact_class=False)

   Specify a set of options that will override the form field's defaults when ``WagtailAdminModelForm`` encounters a given model field type.

   :param model_field_class: Specifies a model field class, such as ``models.CharField``; the override will take effect on fields that are instances of this class.
   :param to: For ``ForeignKey`` fields, indicates the model that the field must point to for the override to take effect.
   :param override: A dict of keyword arguments to be passed to the form field's ``__init__`` method, such as ``widget``.
   :param exact_class: If true, the override will only take effect for model fields that are of the exact type given by ``model_field_class``, and not a subclass of it.
```

For example, if the app `wagtail.videos` implements a `Video` model and a `VideoChooser` form widget, the following AppConfig definition will ensure that `WagtailAdminModelForm` selects `VideoChooser` as the form widget for any foreign keys pointing to `Video`:

```python
from django.apps import AppConfig
from django.db.models import ForeignKey


class WagtailVideosAppConfig(AppConfig):
    name = 'wagtail.videos'
    label = 'wagtailvideos'

    def ready(self):
        from wagtail.admin.forms.models import register_form_field_override
        from .models import Video
        from .widgets import VideoChooser
        register_form_field_override(ForeignKey, to=Video, override={'widget': VideoChooser})
```

Wagtail's edit views for pages, snippets and ModelAdmin use `WagtailAdminModelForm` as standard, so this change will take effect across the Wagtail admin; a foreign key to `Video` on a page model will automatically use the `VideoChooser` widget, with no need to specify this explicitly.

## Panels

Panels (also known as edit handlers until Wagtail 3.0) are Wagtail's mechanism for specifying the content and layout of a model form without having to write a template. They are used for the editing interface for pages and snippets, as well as the [ModelAdmin](/reference/contrib/modeladmin/index) and [site settings](/reference/contrib/settings) contrib modules.

See [](/reference/pages/panels) for the set of panel types provided by Wagtail. All panels inherit from the base class `wagtail.admin.panels.Panel`. A single panel object (usually `ObjectList` or `TabbedInterface`) exists at the top level and is the only one directly accessed by the view code; panels containing child panels inherit from the base class `wagtail.admin.panels.PanelGroup` and take care of recursively calling methods on their child panels where appropriate.

A view performs the following steps to render a model form through the panels mechanism:

-   The top-level panel object for the model is retrieved. Usually this is done by looking up the model's `edit_handler` property and falling back on an `ObjectList` consisting of children given by the model's `panels` property. However, it may come from elsewhere - for example, the ModelAdmin module allows defining it on the ModelAdmin configuration object.
-   The view calls `bind_to_model` on the top-level panel, passing the model class, and this returns a clone of the panel with a `model` property. As part of this process the `on_model_bound` method is invoked on each child panel, to allow it to perform additional initialisation that requires access to the model (for example, this is where `FieldPanel` retrieves the model field definition).
-   The view then calls `get_form_class` on the top-level panel to retrieve a ModelForm subclass that can be used to edit the model. This proceeds as follows:
    -   Retrieve a base form class from the model's `base_form_class` property, falling back on `wagtail.admin.forms.WagtailAdminModelForm`
    -   Call `get_form_options` on each child panel - which returns a dictionary of properties including `fields` and `widgets` - and merge the results into a single dictionary
    -   Construct a subclass of the base form class, with the options dict forming the attributes of the inner `Meta` class.
-   An instance of the form class is created as per a normal Django form view.
-   The view then calls `get_bound_panel` on the top-level panel, passing `instance`, `form` and `request` as keyword arguments. This returns a `BoundPanel` object, which follows [the template component API](/extending/template_components). Finally, the `BoundPanel` object (and its media definition) is rendered onto the template.

New panel types can be defined by subclassing `wagtail.admin.panels.Panel` - see [](/reference/panel_api).
