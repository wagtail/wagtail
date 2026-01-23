(custom_streamfield_blocks)=

# How to build custom StreamField blocks

(custom_editing_interfaces_for_structblock)=

## Custom editing interfaces for `StructBlock`

The editing interface for a `StructBlock` can be configured in several ways, depending on the level of customization required.

(structblock_custom_classes_and_attributes)=

### Adding custom classes and attributes

To customize the styling of a `StructBlock` as it appears in the page editor, you can specify a `form_classname` attribute (either as a keyword argument to the `StructBlock` constructor, or in a subclass's `Meta`) to override the default value of `struct-block`:

```python
class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageChooserBlock(required=False)
    biography = blocks.RichTextBlock()

    class Meta:
        icon = "user"
        form_classname = "person-block struct-block"
        form_attrs = {
            # This block has additional customizations enabled
            "data-controller": "magic",
            "data-action": "click->magic#abracadabra",
        }
```

You can then provide custom CSS for this block, targeted at the specified classname, by using the [](insert_global_admin_css) hook.

```{note}
If you specify a value for `form_classname`, it will overwrite the classes that are already applied to `StructBlock`. You may need to include the default `struct-block` class if you have custom code or use a third-party package that relies on it.
```

If you want to add custom attributes other than `class` on a `StructBlock` in the page editor, you can specify a `form_attrs` attribute (either as a keyword argument to the `StructBlock` constructor, or in a subclass's `Meta`) to add any additional attributes.

For example, you can use the custom attributes to [attach Stimulus controllers](extending_client_side_stimulus) to the block.

```{note}
Any attributes in `form_attrs` will take precedence over the default attributes that Wagtail applies to `StructBlock` elements in the page editor, such as `class`.
```

(structblock_initial_collapsible)=

### Customizing the initial collapsible state

In addition, the `StructBlock`'s `Meta` class also accepts a `collapsed` attribute. When set to `True`, the block is initially displayed in a collapsed state in the editing interface. This can be useful for blocks with many sub-blocks, or blocks that are not expected to be edited frequently. Note that this only applies to `StructBlock` inside another `StructBlock`. If the `StructBlock` is within a `StreamBlock` or `ListBlock`, the initial state will follow the parent block's `collapsed` option.

```python
class SettingsBlock(blocks.StructBlock):
    theme = ChoiceBlock(
        choices=[
            ("banana", "Banana"),
            ("cherry", "Cherry"),
            ("lime", "Lime"),
        ],
        required=False,
        default="banana",
        help_text="Select the theme for the block",
    )
    available = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Whether this person is available",
    )

    class Meta:
        icon = "cog"
        # This block will be initially collapsed
        collapsed = True
        # The block's summary label when collapsed
        label_format = "Theme: {theme}, Available: {available}"


class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageChooserBlock(required=False)
    biography = blocks.RichTextBlock()
    settings = SettingsBlock()

    class Meta:
        icon = "user"
```

(structblock_custom_order_and_grouping)=

### Changing the order and grouping of child blocks

```{versionadded} 7.3
The `form_layout` attribute and `BlockGroup` were added.
```

By default, the child blocks of a `StructBlock` are rendered in the order they are defined on the block class. However, you can customize this order by specifying a `form_layout` attribute in the block's `Meta` class.

If you need to change the order of child blocks, you can provide a list of block names:

```python
class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageChooserBlock(required=False)
    biography = blocks.RichTextBlock()

    class Meta:
        form_layout = [
            "photo",
            "surname",
            "first_name",
            "biography",
        ]
```

The `form_layout` attribute also accepts a `BlockGroup` instance. Using a `BlockGroup` allows you to group multiple blocks together without having to split them into nested `StructBlock`s.

The `BlockGroup` class accepts a list of `children` block names, as well as optional list of `settings` block names. Blocks inside the `settings` list will be hidden by default, and can be revealed by clicking a "Settings" button in the block's actions.

For example, blocks inside `SettingsBlock` from the previous example can be put directly into the `PersonBlock`, to be grouped under a "Settings" button:

```python
from wagtail.blocks import BlockGroup


class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageChooserBlock(required=False)
    biography = blocks.RichTextBlock()
    theme = ChoiceBlock(
        choices=[
            ("banana", "Banana"),
            ("cherry", "Cherry"),
            ("lime", "Lime"),
        ],
        required=False,
        default="banana",
        help_text="Select the theme for the block",
    )
    available = blocks.BooleanBlock(
        required=False,
        default=True,
        help_text="Whether this person is available",
    )

    class Meta:
        icon = "user"
        form_layout = BlockGroup(
            children=[
                "photo",
                "surname",
                "first_name",
                "biography",
            ],
            settings=[
                "theme",
                "available",
            ]
        )
```

You can nest `BlockGroup`s to group multiple blocks inside a collapsible panel. In addition to `children` and `settings` arguments, nested `BlockGroup`s also accept `heading`, `classname`, `help_text`, `icon`, `attrs`, and `label_format` arguments, which are used to customize the appearance of the group in the editing interface. To set a group to be initially collapsed, add the `collapsed` class to the `classname` argument.

```python
class PersonBlock(blocks.StructBlock):
    ...  # as above

    class Meta:
        form_layout = BlockGroup(
            children=[
                # Can mix BlockGroups and individual blocks
                "photo",
                BlockGroup(
                    children=["surname", "first_name"],
                    heading="Basic info",
                    label_format="{first_name} {surname}",
                ),
                BlockGroup(
                    children=["biography"],
                    heading="Biography",
                    classname="collapsed",
                    icon="edit"
                ),
            ],
            settings=[
                "theme",
                "available",
                # BlockGroups can also be nested inside settings if desired
            ]
        )
```

You can also override `get_form_layout` on the block class to modify the `BlockGroup` programmatically, which can be useful when extending a base block class:

```python
from copy import deepcopy


class EmployeeBlock(PersonBlock):
    role = blocks.CharBlock()
    shown = blocks.BooleanBlock(required=False, default=True)

    def get_form_layout(self):
        # Use deepcopy to avoid modifying the parent's layout in-place
        form_layout = deepcopy(super().get_form_layout())
        # Add new blocks to suitable locations
        form_layout.children[1].children += ["role"]
        form_layout.settings += ["shown"]
        return form_layout
```

Note that the use of `BlockGroup`s only affects the editing interface. The data structure of the block remains unchanged. This means that the values of the child blocks can still be accessed in the same way, such as `block.value['first_name']`.

Refer to the [`BlockGroup`](wagtail.blocks.BlockGroup) documentation for more details on its available attributes and methods.

(structblock_custom_template)=

### Customizing the template of `StructBlock` forms

For more extensive customizations that require changes to the HTML markup as well, you can override the `form_template` attribute in `Meta` to specify your own template path. The following variables are available on this template:

**`children`**\
An `OrderedDict` of `BoundBlock`s for all of the child blocks making up this `StructBlock`. When using a `BlockGroup` as the `Meta.form_layout`, this will only include blocks listed in `children`.

**`settings`**\
An `OrderedDict` of `BoundBlock`s for any blocks listed in the `settings` when using a `BlockGroup` as the `Meta.form_layout`.

**`help_text`**\
The help text for this block, if specified.

**`classname`**\
The class name passed as `form_classname` (defaults to `struct-block`).

**`collapsed`**\
The initial collapsible state of the block (defaults to `False`).

**`block_definition`**\
The `StructBlock` instance that defines this block.

**`prefix`**\
The prefix used on form fields for this block instance, guaranteed to be unique across the form.

To add additional variables, you can override the block's `get_form_context` method:

```python
class PersonBlock(blocks.StructBlock):
    first_name = blocks.CharBlock()
    surname = blocks.CharBlock()
    photo = ImageChooserBlock(required=False)
    biography = blocks.RichTextBlock()

    def get_form_context(self, value, prefix='', errors=None):
        context = super().get_form_context(value, prefix=prefix, errors=errors)
        context['suggested_first_names'] = ['John', 'Paul', 'George', 'Ringo']
        return context

    class Meta:
        icon = 'user'
        form_template = 'myapp/block_forms/person.html'
```

A form template for a StructBlock must include the output of `render_form` for each child block in the `children` dict, inside a container element with a `data-contentpath` attribute equal to the block's name. This attribute is used by the commenting framework to attach comments to the correct fields. The StructBlock's form template is also responsible for rendering labels for each field, but this (and all other HTML markup) can be customized as you see fit. The template below replicates the default StructBlock form rendering:

```html+django
{% load wagtailadmin_tags  %}

<div class="{{ classname }}">
    {% if help_text %}
        <span>
            <div class="help">
                {% icon name="help" classname="default" %}
                {{ help_text }}
            </div>
        </span>
    {% endif %}

    <div data-block-settings>
        {% for child in settings.values %}
            <div class="w-field" data-field data-contentpath="{{ child.block.name }}">
                {% if child.block.label %}
                    <label class="w-field__label" {% if child.id_for_label %}for="{{ child.id_for_label }}"{% endif %}>{{ child.block.label }}{% if child.block.required %}<span class="w-required-mark">*</span>{% endif %}</label>
                {% endif %}
                {{ child.render_form }}
            </div>
        {% endfor %}
    </div>

    {% for child in children.values %}
        <div class="w-field" data-field data-contentpath="{{ child.block.name }}">
            {% if child.block.label %}
                <label class="w-field__label" {% if child.id_for_label %}for="{{ child.id_for_label }}"{% endif %}>{{ child.block.label }}{% if child.block.required %}<span class="w-required-mark">*</span>{% endif %}</label>
            {% endif %}
            {{ child.render_form }}
        </div>
    {% endfor %}
</div>
```

If the `Meta.form_layout` is a `BlockGroup` that uses `settings`, those blocks must be rendered inside a container element with a `data-block-settings` attribute, as shown above. The container will be hidden by default, and can be revealed by clicking a "Settings" button in the block's actions.

```{note}
Nested `BlockGroup`s are not supported when using a custom `form_template`. There is a system check to prevent this misconfiguration.
```

(custom_streamfield_blocks_media)=

## Additional JavaScript on `StructBlock` forms

Often it may be desirable to attach custom JavaScript behavior to a StructBlock form. For example, given a block such as:

```python
class AddressBlock(StructBlock):
    street = CharBlock()
    town = CharBlock()
    state = CharBlock(required=False)
    country = ChoiceBlock(choices=[
        ('us', 'United States'),
        ('ca', 'Canada'),
        ('mx', 'Mexico'),
    ])
```

we may wish to disable the 'state' field when a country other than United States is selected. Since new blocks can be added dynamically, we need to integrate with StreamField's own front-end logic to ensure that our custom JavaScript code is executed when a new block is initialized.

StreamField uses the [telepath](https://wagtail.github.io/telepath/) library to map Python block classes such as `StructBlock` to a corresponding JavaScript implementation. These JavaScript implementations can be accessed through the `window.wagtailStreamField.blocks` namespace, as the following classes:

-   `FieldBlockDefinition`
-   `ListBlockDefinition`
-   `StaticBlockDefinition`
-   `StreamBlockDefinition`
-   `StructBlockDefinition`

First, we define a telepath adapter for `AddressBlock`, so that it uses our own JavaScript class in place of the default `StructBlockDefinition`. This can be done in the same module as the `AddressBlock` definition:

```python
from wagtail.blocks.struct_block import StructBlockAdapter
from wagtail.admin.telepath import register
from django import forms
from django.utils.functional import cached_property

class AddressBlockAdapter(StructBlockAdapter):
    js_constructor = 'myapp.blocks.AddressBlock'

    @cached_property
    def media(self):
        structblock_media = super().media
        return forms.Media(
            js=structblock_media._js + ['js/address-block.js'],
            css=structblock_media._css
        )

register(AddressBlockAdapter(), AddressBlock)
```

```{versionchanged} 7.1
The `register` function should now be imported from `wagtail.admin.telepath` rather than `wagtail.telepath`.
```

Here `'myapp.blocks.AddressBlock'` is the identifier for our JavaScript class that will be registered with the telepath client-side code, and `'js/address-block.js'` is the file that defines it (as a path within any static file location recognized by Django). This implementation subclasses StructBlockDefinition and adds our custom code to the `render` method:

```javascript
class AddressBlockDefinition extends window.wagtailStreamField.blocks
    .StructBlockDefinition {
    render(placeholder, prefix, initialState, initialError) {
        const block = super.render(
            placeholder,
            prefix,
            initialState,
            initialError,
        );

        const stateField = document.getElementById(prefix + '-state');
        const countryField = document.getElementById(prefix + '-country');
        const updateStateInput = () => {
            if (countryField.value == 'us') {
                stateField.removeAttribute('disabled');
            } else {
                stateField.setAttribute('disabled', true);
            }
        };
        updateStateInput();
        countryField.addEventListener('change', updateStateInput);

        return block;
    }
}
window.telepath.register('myapp.blocks.AddressBlock', AddressBlockDefinition);
```

(custom_value_class_for_structblock)=

## Additional methods and properties on `StructBlock` values

When rendering StreamField content on a template, StructBlock values are represented as `dict`-like objects where the keys correspond to the names of the child blocks. Specifically, these values are instances of the class `wagtail.blocks.StructValue`.

Sometimes, it's desirable to make additional methods or properties available on this object. For example, given a StructBlock that represents either an internal or external link:

```python
class LinkBlock(StructBlock):
    text = CharBlock(label="link text", required=True)
    page = PageChooserBlock(label="page", required=False)
    external_url = URLBlock(label="external URL", required=False)
```

you may want to make a `url` property available, that returns either the page URL or external URL depending on which one was filled in. A common mistake is to define this property on the block class itself:

```python
class LinkBlock(StructBlock):
    text = CharBlock(label="link text", required=True)
    page = PageChooserBlock(label="page", required=False)
    external_url = URLBlock(label="external URL", required=False)

    @property
    def url(self):  # INCORRECT - will not work
        return self.external_url or self.page.url
```

This does not work because the value as seen in the template is not an instance of `LinkBlock`. `StructBlock` instances only serve as specifications for the block's behavior, and do not hold block data in their internal state - in this respect, they are similar to Django's form widget objects (which provide methods for rendering a given value as a form field, but do not hold on to the value itself).

Instead, you should define a subclass of `StructValue` that implements your custom property or method. Within this method, the block's data can be accessed as `self['page']` or `self.get('page')`, since `StructValue` is a dict-like object.

```python
from wagtail.blocks import StructValue


class LinkStructValue(StructValue):
    def url(self):
        external_url = self.get('external_url')
        page = self.get('page')
        return external_url or page.url
```

Once this is defined, set the block's `value_class` option to instruct it to use this class rather than a plain StructValue:

```python
class LinkBlock(StructBlock):
    text = CharBlock(label="link text", required=True)
    page = PageChooserBlock(label="page", required=False)
    external_url = URLBlock(label="external URL", required=False)

    class Meta:
        value_class = LinkStructValue
```

Your extended value class methods will now be available in your template:

```html+django
{% for block in page.body %}
    {% if block.block_type == 'link' %}
        <a href="{{ link.value.url }}">{{ link.value.text }}</a>
    {% endif %}
{% endfor %}
```

## Custom block types

If you need to implement a custom UI, or handle a datatype that is not provided by Wagtail's built-in block types (and cannot be built up as a structure of existing fields), it is possible to define your own custom block types. For further guidance, refer to the source code of Wagtail's built-in block classes.

For block types that simply wrap an existing Django form field, Wagtail provides an abstract class `wagtail.blocks.FieldBlock` as a helper. Subclasses should set a `field` property that returns the form field object:

```python
class IPAddressBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, **kwargs):
        self.field = forms.GenericIPAddressField(required=required, help_text=help_text)
        super().__init__(**kwargs)
```

Since the StreamField editing interface needs to create blocks dynamically, certain complex widget types will need additional JavaScript code to define how to render and populate them on the client-side. If a field uses a widget type that does not inherit from one of the classes inheriting from `django.forms.widgets.Input`, `django.forms.Textarea`, `django.forms.Select` or `django.forms.RadioSelect`, or has customized client-side behavior to the extent where it is not possible to read or write its data simply by accessing the form element's `value` property, you will need to provide a JavaScript handler object, implementing the methods detailed on [](streamfield_widget_api).

## Handling block definitions within migrations

As with any model field in Django, any changes to a model definition that affect a StreamField will result in a migration file that contains a 'frozen' copy of that field definition. Since a StreamField definition is more complex than a typical model field, there is an increased likelihood of definitions from your project being imported into the migration -- which would cause problems later on if those definitions are moved or deleted.

To mitigate this, StructBlock, StreamBlock, and ChoiceBlock implement additional logic to ensure that any subclasses of these blocks are deconstructed to plain instances of StructBlock, StreamBlock and ChoiceBlock -- in this way, the migrations avoid having any references to your custom class definitions. This is possible because these block types provide a standard pattern for inheritance, and know how to reconstruct the block definition for any subclass that follows that pattern.

If you subclass any other block class, such as `FieldBlock`, you will need to either keep that class definition in place for the lifetime of your project, or implement a [custom deconstruct method](inv:django#custom-deconstruct-method) that expresses your block entirely in terms of classes that are guaranteed to remain in place. Similarly, if you customize a StructBlock, StreamBlock, or ChoiceBlock subclass to the point where it can no longer be expressed as an instance of the basic block type -- for example, if you add extra arguments to the constructor -- you will need to provide your own `deconstruct` method.
