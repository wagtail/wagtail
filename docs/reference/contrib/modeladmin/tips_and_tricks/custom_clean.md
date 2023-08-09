(modeladmin_custom_clean)=

# Adding a custom clean method to your ModelAdmin models

The simplest way is to extend your ModelAdmin model and add a clean() model to it. For example:

```python
from django import forms
from django.db import models

class ModelAdminModel(models.Model):
    def clean(self):
        if self.image.width < 1920 or self.image.height < 1080:
            raise forms.ValidationError("The image must be at least 1920x1080 pixels in size.")
```

This will run the clean and raise the `ValidationError` whenever you save the model and the check fails. The error will be displayed at the top of the wagtail admin.

If you want more fine grained-control you can add a custom `clean()` method to the `WagtailAdminPageForm` of your model.
You can override the form of your ModelAdmin in a similar matter as wagtail Pages.

So, create a custom `WagtailAdminPageForm`:

```python
from wagtail.admin.forms import WagtailAdminPageForm

class ModelAdminModelForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get("image")
        if image and image.width < 1920 or image.height < 1080:
            self.add_error("image", "The image must be at least 1920x1080px")

        return cleaned_data
```

And then set the `base_form_class` of your model:

```python
from django.db import models

class ModelAdminModel(models.Model):
    base_form_class = ModelAdminModelForm
```

Using `self.add_error` will display the error to the particular field that has the error.
