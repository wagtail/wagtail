(custom_account_settings)=

# Customising the user account settings form

This document describes how to customise the user account settings form that can be found by clicking "Account settings"
at the bottom of the main menu.

## Adding new panels

Each panel on this form is a separate model form which can operate on an instance of either the user model, or the {class}`wagtail.users.models.UserProfile`.

### Basic example

Here is an example of how to add a new form that operates on the user model:

```python
# forms.py

from django import forms
from django.contrib.auth import get_user_model

class CustomSettingsForm(forms.ModelForm):

    class Meta:
        model = get_user_model()
        fields = [...]
```

```python
# hooks.py

from wagtail.admin.views.account import BaseSettingsPanel
from wagtail import hooks
from .forms import CustomSettingsForm

@hooks.register('register_account_settings_panel')
class CustomSettingsPanel(BaseSettingsPanel):
    name = 'custom'
    title = "My custom settings"
    order = 500
    form_class = CustomSettingsForm
    form_object = 'user'
```

The attributes are as follows:

-   `name` - A unique name for the panel. All form fields are prefixed with this name, so it must be lowercase and cannot contain symbols -
-   `title` - The heading that is displayed to the user
-   `order` - Used to order panels on a tab. The builtin Wagtail panels start at `100` and increase by `100` for each panel.
-   `form_class` - A `ModelForm` subclass that operates on a user or a profile
-   `form_object` - Set to `user` to operate on the user, and `profile` to operate on the profile
-   `tab` (optional) - Set which tab the panel appears on.
-   `template_name` (optional) - Override the default template used for rendering the panel

## Operating on the `UserProfile` model

To add a panel that alters data on the user's {class}`wagtail.users.models.UserProfile` instance, set `form_object` to `'profile'`:

```python
# forms.py

from django import forms
from wagtail.users.models import UserProfile

class CustomProfileSettingsForm(forms.ModelForm):

    class Meta:
        model = UserProfile
        fields = [...]
```

```python
# hooks.py

from wagtail.admin.views.account import BaseSettingsPanel
from wagtail import hooks
from .forms import CustomProfileSettingsForm

@hooks.register('register_account_settings_panel')
class CustomSettingsPanel(BaseSettingsPanel):
    name = 'custom'
    title = "My custom settings"
    order = 500
    form_class = CustomProfileSettingsForm
    form_object = 'profile'
```

## Creating new tabs

You can define a new tab using the `SettingsTab` class:

```python
# hooks.py

from wagtail.admin.views.account import BaseSettingsPanel, SettingsTab
from wagtail import hooks
from .forms import CustomSettingsForm

custom_tab = SettingsTab('custom', "Custom settings", order=300)

@hooks.register('register_account_settings_panel')
class CustomSettingsPanel(BaseSettingsPanel):
    name = 'custom'
    title = "My custom settings"
    tab = custom_tab
    order = 100
    form_class = CustomSettingsForm
```

`SettingsTab` takes three arguments:

-   `name` - A slug to use for the tab (this is placed after the `#` when linking to a tab)
-   `title` - The display name of the title
-   `order` - The order of the tab. The builtin Wagtail tabs start at `100` and increase by `100` for each tab

## Customising the template

You can provide a custom template for the panel by specifying a template name:

```python
# hooks.py

from wagtail.admin.views.account import BaseSettingsPanel
from wagtail import hooks
from .forms import CustomSettingsForm

@hooks.register('register_account_settings_panel')
class CustomSettingsPanel(BaseSettingsPanel):
    name = 'custom'
    title = "My custom settings"
    order = 500
    form_class = CustomSettingsForm
    template_name = 'myapp/admin/custom_settings.html'
```

```html+django

{# templates/myapp/admin/custom_settings.html #}

{# This is the default template Wagtail uses, which just renders the form #}

<ul class="fields">
    {% for field in form %}
        {% include "wagtailadmin/shared/field_as_li.html" with field=field %}
    {% endfor %}
</ul>
```
