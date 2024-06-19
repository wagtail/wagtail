(streamfield_validation)=

# StreamField validation

All StreamField blocks implement a `clean` method which accepts a block value and returns a cleaned version of that value, or raises a `ValidationError` if the value fails validation. Built-in validation rules, such as checking that a URLBlock value is a correctly-formatted URL, are implemented through this method. Additionally, for blocks that act as containers for other blocks, such as StructBlock, the `clean` method recursively calls the `clean` methods of its child blocks and handles raising validation errors back to the caller as required.

The `clean` method can be overridden on block subclasses to implement custom validation logic. For example, a StructBlock that requires either one of its child blocks to be filled in could be implemented as follows:

```python
from django.core.exceptions import ValidationError
from wagtail.blocks import StructBlock, PageChooserBlock, URLBlock

class LinkBlock(StructBlock):
    page = PageChooserBlock(required=False)
    url = URLBlock(required=False)

    def clean(self, value):
        result = super().clean(value)
        if not(result['page'] or result['url']):
            raise ValidationError("Either page or URL must be specified")
        return result
```

```{note}
The validation of the blocks in the `StreamField` happens through the form field (`wagtail.blocks.base.BlockField`), not the model field (`wagtail.fields.StreamField`).

This means that calling validation methods on your page instance (such as `my_page.full_clean()`) won't catch invalid blocks in the `StreamField` data.

This should only be relevant when the data in the `StreamField` is added programmatically, through other paths than the form field.
```

## Controlling where error messages are rendered

In the above example, an exception of type `ValidationError` is raised, which causes the error to be attached and rendered against the StructBlock as a whole. For more control over where the error appears, the exception class `wagtail.blocks.StructBlockValidationError` can be raised instead. The constructor for this class accepts the following arguments:

-   `non_block_errors` - a list of error messages or `ValidationError` instances to be raised against the StructBlock as a whole
-   `block_errors` - a dict of `ValidationError` instances to be displayed against specific child blocks of the StructBlock, where the key is the child block's name

The following example demonstrates raising a validation error attached to the 'description' block within the StructBlock:

```python
from django.core.exceptions import ValidationError
from wagtail.blocks import CharBlock, StructBlock, StructBlockValidationError, TextBlock

class TopicBlock(StructBlock):
    keyword = CharBlock()
    description = TextBlock()

    def clean(self, value):
        result = super().clean(value)
        if result["keyword"] not in result["description"]:
            raise StructBlockValidationError(block_errors={
                "description": ValidationError("Description must contain the keyword")
            })
        return result
```

ListBlock and StreamBlock also have corresponding exception classes `wagtail.blocks.ListBlockValidationError` and `wagtail.blocks.StreamBlockValidationError`, which work similarly, except that the keys of the `block_errors` dict are the numeric indexes of the blocks where the errors are to be attached:

```python
from django.core.exceptions import ValidationError
from wagtail.blocks import ListBlock, ListBlockValidationError

class AscendingListBlock(ListBlock):
    # example usage:
    # price_list = AscendingListBlock(FloatBlock())

    def clean(self, value):
        result = super().clean(value)
        errors = {}
        for i in range(1, len(result)):
            if result[i] < result[i - 1]:
                errors[i] = ValidationError("Values must be in ascending order")

        if errors:
            raise ListBlockValidationError(block_errors=errors)

        return result
```
