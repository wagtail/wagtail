# General coding guidelines

## Language

British English is preferred for user-facing text; this text should also be marked for translation (using the `django.utils.translation.gettext` function and `{% translate %}` template tag, for example). However, identifiers within code should use American English if the British or international spelling would conflict with built-in language keywords; for example, CSS code should consistently use the spelling `color` to avoid inconsistencies like `background-color: $colour-red`. American English is also the preferred spelling style when writing documentation. Learn more about our documentation writing style in [](writing_style_guide).

## File names

Where practical, try to adhere to the existing convention of file names within the folder where added.

Examples:

-   Django templates - `lower_snake_case.html`
-   Documentation - `lower_snake_case.md`

## Naming conventions

### Use `classname` in Python / HTML template tag variables

`classname` is preferred for any API / interface or Django template variables that need to output an HTML class.

#### Django template tag

Example template tag definition

```python
@register.inclusion_tag("wagtailadmin/shared/dialog/dialog_toggle.html")
def dialog_toggle(dialog_id, classname="", text=None):
    return {
        "classname": classname,
        "text": text,
    }
```

Example template

```html+django
{% comment "text/markdown" %}

    Variables accepted by this template:

    - `classname` - {string?} if present, adds classname to button
    - `dialog_id` - {string} unique id to use to reference the modal which will be triggered

{% endcomment %}

<button type="button" class="{{ classname }}" data-a11y-dialog-show="{{ dialog_id }}">
    {{ text }}
</button>
```

Example usage

```html+django
{% dialog_toggle classname='button button-primary' %}
```

### Python / Django class driven content

```python
class Panel:
    def __init__(self, heading="", classname="", help_text="", base_form_class=None):
        self.heading = heading
        self.classname = classname
```

#### Details

| Convention    | Usage                                                                                                               |
| ------------- | ------------------------------------------------------------------------------------------------------------------- |
| `classname`   | ✅ Preferred for any new code.                                                                                      |
| `class`       | ✳️ Only if used as part of a generic `attrs`-like dict; however avoid due to conflicts with Python `class` keyword. |
| `classnames`  | ❌ Avoid for new code.                                                                                              |
| `class_name`  | ❌ Avoid for new code.                                                                                              |
| `class_names` | ❌ Avoid for new code.                                                                                              |
| `className`   | ❌ Avoid for new code.                                                                                              |
| `classNames`  | ❌ Avoid for new code.                                                                                              |
