# Python coding guidelines

## PEP8

We ask that all Python contributions adhere to the [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide.
All files should be formatted using the [black](https://github.com/psf/black) auto-formatter. This will be
run by `pre-commit` if that is configured.

-   The project repository includes an `.editorconfig` file. We recommend using
    a text editor with [EditorConfig](https://editorconfig.org/) support to avoid indentation and
    whitespace issues. Python and HTML files use 4 spaces for indentation.

In addition, import lines should be sorted according to [isort](https://pycqa.github.io/isort/) 5.6.4 rules.
If you have installed Wagtail's testing dependencies (`pip install -e '.[testing]'`), you can check your code by
running `make lint`. You can also just check python related linting by running `make lint-server`.

You can run all Python formatting with `make format`. Similar to linting you can format python/template only files
by running `make format-server`.

## Django compatibility

Wagtail is written to be compatible with multiple versions of Django. Sometimes, this requires running one piece of code for recent version of Django, and another piece of code for older versions of Django. In these cases, always check which version of Django is being used by inspecting `django.VERSION`:

```python
import django

if django.VERSION >= (1, 9):
    # Use new attribute
    related_field = field.rel
else:
    # Use old, deprecated attribute
    related_field = field.related
```

Always compare against the version using greater-or-equals (`>=`), so that code for newer versions of Django is first.

Do not use a `try ... except` when seeing if an object has an attribute or method introduced in a newer versions of Django, as it does not clearly express why the `try ... except` is used. An explicit check against the Django version makes the intention of the code very clear.

```python
# Do not do this
try:
    related_field = field.rel
except AttributeError:
    related_field = field.related
```

If the code needs to use something that changed in a version of Django many times, consider making a function that encapsulates the check:

```python
import django

def related_field(field):
    if django.VERSION >= (1, 9):
        return field.rel
    else:
        return field.related
```

If a new function has been introduced by Django that you think would be very useful for Wagtail, but is not available in older versions of Django that Wagtail supports, that function can be copied over in to Wagtail. If the user is running a new version of Django that has the function, the function should be imported from Django. Otherwise, the version bundled with Wagtail should be used. A link to the Django source code where this function was taken from should be included:

```python
import django

if django.VERSION >= (1, 9):
    from django.core.validators import validate_unicode_slug
else:
    # Taken from https://github.com/django/django/blob/1.9/django/core/validators.py#L230
    def validate_unicode_slug(value):
            # Code left as an exercise to the reader
            pass
```

## Tests

Wagtail has a suite of tests, which we are committed to improving and expanding. See [](testing).

We run continuous integration to ensure that no commits or pull requests introduce test failures. If your contributions add functionality to Wagtail, please include the additional tests to cover it; if your contributions alter existing functionality, please update the relevant tests accordingly.
