# General coding guidelines

## Use of generative AI

AI assistance when working on Wagtail is permitted. Purely AI-generated contributions are not - if we wanted those, we would prompt an AI agent ourselves.

As a contributor to the project, we would like you to consider what value you are providing beyond your ability to paste a bug report into an LLM. Even if you are not familiar with the Wagtail codebase, your experience as a Wagtail user or site builder is still valuable for providing guidance on how a feature should behave, how and where it should be documented, or manually replicating an issue and verifying that it has been fixed, perhaps with screenshots. All of this is information that we would like to see in a PR, as it demonstrates that a human has understood and thought about the issue being fixed.

For this reason, we ask you to write the pull request description yourself, and not offload that task to an AI agent.

If you use generative AI for your contribution, please fill in the "AI usage" portion of the PR description. For example:

> _"This pull request includes code written by Claude Code. I have verified in-browser that this fixes the issue."_

### Acceptable uses

-  Gaining understanding of the existing Wagtail code
-  Assistance with written English for code comments, documentation and pull request descriptions
-  Supplementing contributor knowledge for code, tests, and documentation

### Unacceptable uses

- Entire work (code changes, documentation update, pull request descriptions) are LLM-generated without there being a clear understanding of the solution implementation from the contributor.
- Responding to questions asked during code review by pasting those questions into an LLM
- Allowing an LLM to make unchecked false statements through the use of stock phrases, such as claiming to have manually tested a bugfix, or claiming to have experience of an issue through a real-world project

We will close those pull requests and issues that are unproductive, so we can focus our limited maintainer capacity elsewhere.

## Language

British English is preferred for user-facing text; this text should also be marked for translation (using the `django.utils.translation.gettext` function and `{% translate %}` template tag, for example).

User-facing errors or field validation should use a well-formed sentence with a period (full stop) at the end.

However, identifiers within code should use American English if the British or international spelling would conflict with built-in language keywords; for example, CSS code should consistently use the spelling `color` to avoid inconsistencies like `background-color: $colour-red`. American English is also the preferred spelling style when writing documentation.

Learn more about our documentation writing style in [](writing_style_guide).

Learn more about how to make content suitable for translations in [](contributing_translations).

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
