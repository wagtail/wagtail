import collections
import itertools
import json
import re
from functools import lru_cache
from importlib import import_module

from django import forms
from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.telepath import JSContext
from wagtail.admin.telepath import register as register_telepath_adapter
from wagtail.utils.templates import template_is_overridden

__all__ = [
    "BaseBlock",
    "Block",
    "BoundBlock",
    "DeclarativeSubBlocksMetaclass",
    "BlockWidget",
    "BlockField",
]


# =========================================
# Top-level superclasses and helper objects
# =========================================


class BaseBlock(type):
    def __new__(mcs, name, bases, attrs):
        meta_class = attrs.pop("Meta", None)

        cls = super().__new__(mcs, name, bases, attrs)

        # Get all the Meta classes from all the bases
        meta_class_bases = [meta_class] + [
            getattr(base, "_meta_class", None) for base in bases
        ]
        meta_class_bases = tuple(filter(bool, meta_class_bases))
        cls._meta_class = type(str(name + "Meta"), meta_class_bases, {})

        return cls


class Block(metaclass=BaseBlock):
    name = ""
    creation_counter = 0
    definition_registry = {}

    TEMPLATE_VAR = "value"
    DEFAULT_PREVIEW_TEMPLATE = "wagtailcore/shared/block_preview.html"

    class Meta:
        label = None
        icon = "placeholder"
        classname = None
        form_attrs = None
        group = ""

    # Attributes of Meta which can legally be modified after the block has been instantiated.
    # Used to implement __eq__. label is not included here, despite it technically being mutable via
    # set_name, since its value must originate from either the constructor arguments or set_name,
    # both of which are captured by the equality test, so checking label as well would be redundant.
    MUTABLE_META_ATTRIBUTES = []

    def __new__(cls, *args, **kwargs):
        # adapted from django.utils.deconstruct.deconstructible; capture the arguments
        # so that we can return them in the 'deconstruct' method
        obj = super().__new__(cls)
        obj._constructor_args = (args, kwargs)
        return obj

    def __init__(self, **kwargs):
        if "classname" in self._constructor_args[1]:
            # Adding this so that migrations are not triggered
            # when form_classname is used instead of classname
            # in the initialisation of the FieldBlock
            classname = self._constructor_args[1].pop("classname")
            self._constructor_args[1].setdefault("form_classname", classname)

        self.meta = self._meta_class()

        for attr, value in kwargs.items():
            setattr(self.meta, attr, value)

        # Increase the creation counter, and save our local copy.
        self.creation_counter = Block.creation_counter
        Block.creation_counter += 1
        self.definition_prefix = "blockdef-%d" % self.creation_counter
        Block.definition_registry[self.definition_prefix] = self

        self.label = self.meta.label or ""

    @classmethod
    def construct_from_lookup(cls, lookup, *args, **kwargs):
        """
        See `wagtail.blocks.definition_lookup.BlockDefinitionLookup`.
        Construct a block instance from the provided arguments, using the given BlockDefinitionLookup
        object to perform any necessary lookups.
        """
        # In the base implementation, no lookups take place - args / kwargs are passed
        # on to the constructor as-is
        return cls(*args, **kwargs)

    def set_name(self, name):
        self.name = name
        if not self.meta.label:
            self.label = capfirst(force_str(name).replace("_", " "))

    def set_meta_options(self, opts):
        """
        Update this block's meta options (out of the ones designated as mutable) from the given dict.
        Used by the StreamField constructor to pass on kwargs that are to be handled by the block,
        since the block object has already been created by that point, e.g.:
        body = StreamField(SomeStreamBlock(), max_num=5)
        """
        for attr, value in opts.items():
            if attr in self.MUTABLE_META_ATTRIBUTES:
                setattr(self.meta, attr, value)
            else:
                raise TypeError(
                    "set_meta_options received unexpected option: %r" % attr
                )

    def value_from_datadict(self, data, files, prefix):
        raise NotImplementedError("%s.value_from_datadict" % self.__class__)

    def value_omitted_from_data(self, data, files, name):
        """
        Used only for top-level blocks wrapped by BlockWidget (i.e.: typically only StreamBlock)
        to inform ModelForm logic on Django >=1.10.2 whether the field is absent from the form
        submission (and should therefore revert to the field default).
        """
        return name not in data

    def bind(self, value, prefix=None, errors=None):
        """
        Return a BoundBlock which represents the association of this block definition with a value
        and a prefix (and optionally, a ValidationError to be rendered).
        BoundBlock primarily exists as a convenience to allow rendering within templates:
        bound_block.render() rather than blockdef.render(value, prefix) which can't be called from
        within a template.
        """
        return BoundBlock(self, value, prefix=prefix, errors=errors)

    def _evaluate_callable(self, value):
        return value() if callable(value) else value

    def get_default(self):
        """
        Return this block's default value (conventionally found in self.meta.default),
        converted to the value type expected by this block. If the default is a callable
        (e.g. a function), it will be evaluated at runtime. This caters for
        the case where that value type is not something that can be expressed statically at
        model definition time (e.g. something like StructValue which incorporates a
        pointer back to the block definition object).
        """
        default = self._evaluate_callable(getattr(self.meta, "default", None))
        return self.normalize(default)

    def clean(self, value):
        """
        Validate value and return a cleaned version of it, or throw a ValidationError if validation fails.
        The thrown ValidationError instance will subsequently be passed to render() to display the
        error message; the ValidationError must therefore include all detail necessary to perform that
        rendering, such as identifying the specific child block(s) with errors, in the case of nested
        blocks. (It is suggested that you use the 'params' attribute for this; using error_list /
        error_dict is unreliable because Django tends to hack around with these when nested.)
        """
        return value

    def normalize(self, value):
        """
        Given a value for any acceptable type for this block (e.g. string or RichText for a RichTextBlock;
        dict or StructValue for a StructBlock), return a value of the block's native type (e.g. RichText
        for RichTextBlock, StructValue for StructBlock). In simple cases this will return the value
        unchanged.
        """
        return value

    def to_python(self, value):
        """
        Convert 'value' from a simple (JSON-serialisable) value to a (possibly complex) Python value to be
        used in the rest of the block API and within front-end templates . In simple cases this might be
        the value itself; alternatively, it might be a 'smart' version of the value which behaves mostly
        like the original value but provides a native HTML rendering when inserted into a template; or it
        might be something totally different (e.g. an image chooser will use the image ID as the clean
        value, and turn this back into an actual image object here).

        For blocks that are usable at the top level of a StreamField, this must also accept any type accepted
        by normalize. (This is because Django calls `Field.to_python` from `Field.clean`.)
        """
        return value

    def bulk_to_python(self, values):
        """
        Apply the to_python conversion to a list of values. The default implementation simply
        iterates over the list; subclasses may optimise this, e.g. by combining database lookups
        into a single query.
        """
        return [self.to_python(value) for value in values]

    def get_prep_value(self, value):
        """
        The reverse of to_python; convert the python value into JSON-serialisable form.
        """
        return value

    def get_form_state(self, value):
        """
        Convert a python value for this block into a JSON-serialisable representation containing
        all the data needed to present the value in a form field, to be received by the block's
        client-side component. Examples of where this conversion is not trivial include rich text
        (where it needs to be supplied in a format that the editor can process, e.g. ContentState
        for Draftail) and page / image / document choosers (where it needs to include all displayed
        data for the selected item, such as title or thumbnail).
        """
        return value

    def get_context(self, value, parent_context=None):
        """
        Return a dict of context variables (derived from the block ``value`` and combined with the
        ``parent_context``) to be used as the template context when rendering this value through a
        template. See :ref:`the usage example <streamfield_get_context>` for more details.
        """

        context = parent_context or {}
        context.update(
            {
                "self": value,
                self.TEMPLATE_VAR: value,
            }
        )
        return context

    def get_template(self, value=None, context=None):
        """
        Return the template to use for rendering the block if specified.
        This method allows for dynamic templates based on the block instance and a given ``value``.
        See :ref:`the usage example <streamfield_get_template>` for more details.
        """
        return getattr(self.meta, "template", None)

    def render(self, value, context=None):
        """
        Return a text rendering of 'value', suitable for display on templates. By default, this will
        use a template (with the passed context, supplemented by the result of get_context) if a
        'template' property is specified on the block, and fall back on render_basic otherwise.
        """
        template = self.get_template(value, context=context)
        if not template:
            return self.render_basic(value, context=context)

        if context is None:
            new_context = self.get_context(value)
        else:
            new_context = self.get_context(value, parent_context=dict(context))

        return mark_safe(render_to_string(template, new_context))

    def get_preview_context(self, value, parent_context=None):
        """
        Return a dict of context variables to be used as the template context
        when rendering the block's preview. The ``value`` argument is the value
        returned by :meth:`get_preview_value`. The ``parent_context`` argument
        contains the following variables:

        - ``request``: The current request object.
        - ``block_def``: The block instance.
        - ``block_class``: The block class.
        - ``bound_block``: A ``BoundBlock`` instance representing the block and its value.

        If :ref:`the global preview template <streamfield_global_preview_template>`
        is used, the block will be rendered as the main content using
        ``{% include_block %}``, which in turn uses :meth:`get_context`. As a
        result, the context returned by this method will be available as the
        ``parent_context`` for ``get_context()`` when the preview is rendered.
        """
        # NOTE: see StreamFieldBlockPreview.base_context for the context variables
        # that can be documented.
        return parent_context or {}

    def get_preview_template(self, value, context=None):
        """
        Return the template to use for rendering the block's preview. The ``value``
        argument is the value returned by :meth:`get_preview_value`. The ``context``
        argument contains the variables listed for the ``parent_context`` argument
        of :meth:`get_preview_context` above (and not the context returned by that
        method itself).

        Note that the preview template is used to render a complete HTML page of
        the preview, not just an HTML fragment for the block. The method returns
        the ``preview_template`` attribute from the block's options if provided,
        and falls back to
        :ref:`the global preview template <streamfield_global_preview_template>`
        otherwise.

        If the global preview template is used, the block will be rendered as the
        main content using ``{% include_block %}``, which in turn uses
        :meth:`get_template`.
        """
        return (
            getattr(self.meta, "preview_template", None)
            or self.DEFAULT_PREVIEW_TEMPLATE
        )

    def get_preview_value(self):
        """
        Return the placeholder value that will be used for rendering the block's
        preview. By default, the value is the ``preview_value`` from the block's
        options if provided. If it's a callable, it will be evaluated at runtime.
        If ``preview_value`` is not provided, the ``default`` is used as fallback.
        This method can also be overridden to provide a dynamic preview value.
        """
        if hasattr(self.meta, "preview_value"):
            value = self._evaluate_callable(self.meta.preview_value)
            return self.normalize(value)
        return self.get_default()

    @cached_property
    def _has_default(self):
        return getattr(self.meta, "default", None) is not None

    @cached_property
    def is_previewable(self):
        """
        Determine whether the block is previewable in the block picker. By
        default, it automatically detects when a custom template is used or the
        :ref:`the global preview template <streamfield_global_preview_template>`
        is overridden and a preview value is provided. If the block is
        previewable by other means, override this property to return ``True``.
        To turn off previews for the block, set it to ``False``.
        """
        has_specific_template = (
            hasattr(self.meta, "preview_template")
            or self.__class__.get_preview_template is not Block.get_preview_template
        )
        has_preview_value = (
            hasattr(self.meta, "preview_value")
            or self._has_default
            or self.__class__.get_preview_context is not Block.get_preview_context
            or self.__class__.get_preview_value is not Block.get_preview_value
        )
        has_global_template = template_is_overridden(
            self.DEFAULT_PREVIEW_TEMPLATE,
            "templates",
        )
        return has_specific_template or (has_preview_value and has_global_template)

    def get_description(self):
        """
        Return the description of the block to be shown to editors as part of the preview.
        For :ref:`field block types <field_block_types>`, it will fall back to
        ``help_text`` if not provided.
        """
        return getattr(self.meta, "description", "")

    def get_api_representation(self, value, context=None):
        """
        Can be used to customise the API response and defaults to the value returned by get_prep_value.
        """
        return self.get_prep_value(value)

    def render_basic(self, value, context=None):
        """
        Return a text rendering of 'value', suitable for display on templates. render() will fall back on
        this if the block does not define a 'template' property.
        """
        return force_str(value)

    def get_searchable_content(self, value):
        """
        Returns a list of strings containing text content within this block to be used in a search engine.
        """
        return []

    def extract_references(self, value):
        return []

    def get_block_by_content_path(self, value, path_elements):
        """
        Given a list of elements from a content path, retrieve the block at that path
        as a BoundBlock object, or None if the path does not correspond to a valid block.
        """
        # In the base case, where a block has no concept of children, the only valid path is
        # the empty one (which refers to the current block).
        if path_elements:
            return None
        else:
            return self.bind(value)

    def check(self, **kwargs):
        """
        Hook for the Django system checks framework -
        returns a list of django.core.checks.Error objects indicating validity errors in the block
        """
        return []

    def _check_name(self, **kwargs):
        """
        Helper method called by container blocks as part of the system checks framework,
        to validate that this block's name is a valid identifier.
        (Not called universally, because not all blocks need names)
        """
        errors = []
        if not self.name:
            errors.append(
                checks.Error(
                    "Block name %r is invalid" % self.name,
                    hint="Block name cannot be empty",
                    obj=kwargs.get("field", self),
                    id="wagtailcore.E001",
                )
            )

        if " " in self.name:
            errors.append(
                checks.Error(
                    "Block name %r is invalid" % self.name,
                    hint="Block names cannot contain spaces",
                    obj=kwargs.get("field", self),
                    id="wagtailcore.E001",
                )
            )

        if "-" in self.name:
            errors.append(
                checks.Error(
                    "Block name %r is invalid" % self.name,
                    "Block names cannot contain dashes",
                    obj=kwargs.get("field", self),
                    id="wagtailcore.E001",
                )
            )

        if self.name and self.name[0].isdigit():
            errors.append(
                checks.Error(
                    "Block name %r is invalid" % self.name,
                    "Block names cannot begin with a digit",
                    obj=kwargs.get("field", self),
                    id="wagtailcore.E001",
                )
            )

        if not errors and not re.match(r"^[_a-zA-Z][_a-zA-Z0-9]*$", self.name):
            errors.append(
                checks.Error(
                    "Block name %r is invalid" % self.name,
                    "Block names should follow standard Python conventions for "
                    "variable names: alphanumeric and underscores, and cannot "
                    "begin with a digit",
                    obj=kwargs.get("field", self),
                    id="wagtailcore.E001",
                )
            )

        return errors

    def id_for_label(self, prefix):
        """
        Return the ID to be used as the 'for' attribute of <label> elements that refer to this block,
        when the given field prefix is in use. Return None if no 'for' attribute should be used.
        """
        return None

    @property
    def required(self):
        """
        Flag used to determine whether labels for this block should display a 'required' asterisk.
        False by default, since Block does not provide any validation of its own - it's up to subclasses
        to define what required-ness means.
        """
        return False

    @cached_property
    def canonical_module_path(self):
        """
        Return the module path string that should be used to refer to this block in migrations.
        """
        # adapted from django.utils.deconstruct.deconstructible
        module_name = self.__module__
        name = self.__class__.__name__

        # Make sure it's actually there and not an inner class
        module = import_module(module_name)
        if not hasattr(module, name):
            raise ValueError(
                "Could not find object %s in %s.\n"
                "Please note that you cannot serialize things like inner "
                "classes. Please move the object into the main module "
                "body to use migrations.\n" % (name, module_name)
            )

        # if the module defines a DECONSTRUCT_ALIASES dictionary, see if the class has an entry in there;
        # if so, use that instead of the real path
        try:
            return module.DECONSTRUCT_ALIASES[self.__class__]
        except (AttributeError, KeyError):
            return f"{module_name}.{name}"

    def deconstruct(self):
        return (
            self.canonical_module_path,
            self._constructor_args[0],
            self._constructor_args[1],
        )

    def deconstruct_with_lookup(self, lookup):
        """
        Like `deconstruct`, but with a `wagtail.blocks.definition_lookup.BlockDefinitionLookupBuilder`
        object available so that any block instances within the definition can be added to the lookup
        table to obtain an ID (potentially shared with other matching block definitions, thus reducing
        the overall definition size) to be used in place of the block. The resulting deconstructed form
        returned here can then be restored into a block object using `Block.construct_from_lookup`.
        """
        # In the base implementation, no substitutions happen, so we ignore the lookup and just call
        # deconstruct
        return self.deconstruct()

    def __eq__(self, other):
        """
        Implement equality on block objects so that two blocks with matching definitions are considered
        equal. Block objects are intended to be immutable with the exception of set_name() and any meta
        attributes identified in MUTABLE_META_ATTRIBUTES, so checking these along with the result of
        deconstruct (which captures the constructor arguments) is sufficient to identify (valid) differences.

        This was implemented as a workaround for a Django <1.9 bug and is quite possibly not used by Wagtail
        any more, but has been retained as it provides a sensible definition of equality (and there's no
        reason to break it).
        """

        if not isinstance(other, Block):
            # if the other object isn't a block at all, it clearly isn't equal.
            return False

            # Note that we do not require the two blocks to be of the exact same class. This is because
            # we may wish the following blocks to be considered equal:
            #
            # class FooBlock(StructBlock):
            #     first_name = CharBlock()
            #     surname = CharBlock()
            #
            # class BarBlock(StructBlock):
            #     first_name = CharBlock()
            #     surname = CharBlock()
            #
            # FooBlock() == BarBlock() == StructBlock([('first_name', CharBlock()), ('surname': CharBlock())])
            #
            # For this to work, StructBlock will need to ensure that 'deconstruct' returns the same signature
            # in all of these cases, including reporting StructBlock as the path:
            #
            # FooBlock().deconstruct() == (
            #     'wagtail.blocks.StructBlock',
            #     [('first_name', CharBlock()), ('surname': CharBlock())],
            #     {}
            # )
            #
            # This has the bonus side effect that the StructBlock field definition gets frozen into
            # the migration, rather than leaving the migration vulnerable to future changes to FooBlock / BarBlock
            # in models.py.

        return (
            self.name == other.name
            and self.deconstruct() == other.deconstruct()
            and all(
                getattr(self.meta, attr, None) == getattr(other.meta, attr, None)
                for attr in self.MUTABLE_META_ATTRIBUTES
            )
        )


class BoundBlock:
    def __init__(self, block, value, prefix=None, errors=None):
        self.block = block
        self.value = value
        self.prefix = prefix
        self.errors = errors

    def render(self, context=None):
        return self.block.render(self.value, context=context)

    def render_as_block(self, context=None):
        """
        Alias for render; the include_block tag will specifically check for the presence of a method
        with this name. (This is because {% include_block %} is just as likely to be invoked on a bare
        value as a BoundBlock. If we looked for a `render` method instead, we'd run the risk of finding
        an unrelated method that just happened to have that name - for example, when called on a
        PageChooserBlock it could end up calling page.render.
        """
        return self.block.render(self.value, context=context)

    def id_for_label(self):
        return self.block.id_for_label(self.prefix)

    def __str__(self):
        """Render the value according to the block's native rendering"""
        return self.block.render(self.value)

    def __repr__(self):
        return "<block {}: {!r}>".format(
            self.block.name or type(self.block).__name__,
            self.value,
        )


class DeclarativeSubBlocksMetaclass(BaseBlock):
    """
    Metaclass that collects sub-blocks declared on the base classes.
    (cheerfully stolen from https://github.com/django/django/blob/main/django/forms/forms.py)
    """

    def __new__(mcs, name, bases, attrs):
        # Collect sub-blocks declared on the current class.
        # These are available on the class as `declared_blocks`
        current_blocks = []
        for key, value in list(attrs.items()):
            if isinstance(value, Block):
                current_blocks.append((key, value))
                value.set_name(key)
                attrs.pop(key)
        current_blocks.sort(key=lambda x: x[1].creation_counter)
        attrs["declared_blocks"] = collections.OrderedDict(current_blocks)

        new_class = super().__new__(mcs, name, bases, attrs)

        # Walk through the MRO, collecting all inherited sub-blocks, to make
        # the combined `base_blocks`.
        base_blocks = collections.OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect sub-blocks from base class.
            if hasattr(base, "declared_blocks"):
                base_blocks.update(base.declared_blocks)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in base_blocks:
                    base_blocks.pop(attr)
        new_class.base_blocks = base_blocks

        return new_class


# ========================
# django.forms integration
# ========================


@register_telepath_adapter
class BlockWidget(forms.Widget):
    """Wraps a block object as a widget so that it can be incorporated into a Django form"""

    def __init__(self, block_def, attrs=None):
        super().__init__(attrs=attrs)
        self.block_def = block_def
        self._js_context = None
        self._block_json = None

    def _build_block_json(self):
        try:
            self._js_context = JSContext()
            self._block_json = json.dumps(self._js_context.pack(self.block_def))
        except Exception as e:  # noqa: BLE001
            raise ValueError("Error while serializing block definition: %s" % e) from e

    @property
    def js_context(self):
        if self._js_context is None:
            self._build_block_json()

        return self._js_context

    @property
    def block_json(self):
        if self._block_json is None:
            self._build_block_json()

        return self._block_json

    def id_for_label(self, prefix):
        # Delegate the job of choosing a label ID to the top-level block.
        # (In practice, the top-level block will typically be a StreamBlock, which returns None.)
        return self.block_def.id_for_label(prefix)

    def render_with_errors(self, name, value, attrs=None, errors=None, renderer=None):
        value_json = json.dumps(self.block_def.get_form_state(value))

        if errors:
            # errors is expected to be an ErrorList consisting of a single validation error
            error = errors.as_data()[0]
            error_json = json.dumps(get_error_json_data(error))
        else:
            error_json = json.dumps(None)

        return format_html(
            """
                <div id="{id}" data-block data-controller="w-block" data-w-block-data-value="{block_json}" data-w-block-arguments-value="[{value_json},{error_json}]"></div>
            """,
            id=name,
            block_json=self.block_json,
            value_json=value_json,
            error_json=error_json,
        )

    def render(self, name, value, attrs=None, renderer=None):
        return self.render_with_errors(
            name, value, attrs=attrs, errors=None, renderer=renderer
        )

    @cached_property
    def media(self):
        return self.js_context.media + forms.Media(
            js=[
                # this will almost certainly be
                # pulled in by the block adapters too
                versioned_static("wagtailadmin/js/telepath/blocks.js"),
            ],
            css={
                "all": [
                    versioned_static("wagtailadmin/css/panels/streamfield.css"),
                ]
            },
        )

    def value_from_datadict(self, data, files, name):
        return self.block_def.value_from_datadict(data, files, name)

    def value_omitted_from_data(self, data, files, name):
        return self.block_def.value_omitted_from_data(data, files, name)

    def telepath_pack(self, context):
        return ("wagtail.widgets.BlockWidget", [])


class BlockField(forms.Field):
    """Wraps a block object as a form field so that it can be incorporated into a Django form"""

    def __init__(self, block=None, **kwargs):
        if block is None:
            raise ImproperlyConfigured("BlockField was not passed a 'block' object")
        self.block = block

        if "widget" not in kwargs:
            kwargs["widget"] = BlockWidget(block)

        super().__init__(**kwargs)

    def clean(self, value):
        from wagtail.blocks.stream_block import StreamBlock

        if isinstance(self.block, StreamBlock):
            # StreamBlock is the only block type that is formally-supported as the top level block
            # of a BlockField, but it's possible that other block types could be used, so check
            # this explicitly.
            # self.block has a `required` attribute that is consistent with the StreamField's `blank`
            # attribute and thus the `required` attribute of BlockField - but if the latter has been
            # assigned dynamically (e.g. by defer_required_fields) we want this to take precedence.
            # We do this through the `ignore_required_constraints` flag recognised by
            # StreamBlock.clean.
            return self.block.clean(
                value, ignore_required_constraints=not self.required
            )
        else:
            return self.block.clean(value)

    def has_changed(self, initial_value, data_value):
        return self.block.get_prep_value(initial_value) != self.block.get_prep_value(
            data_value
        )


@lru_cache(maxsize=None)
def get_help_icon():
    return render_to_string(
        "wagtailadmin/shared/icon.html", {"name": "help", "classname": "default"}
    )


def get_error_json_data(error):
    """
    Translate a ValidationError instance raised against a block (which may potentially be a
    ValidationError subclass specialised for a particular block type) into a JSON-serialisable dict
    consisting of one or both of:
    messages: a list of error message strings to be displayed against the block
    blockErrors: a structure specific to the block type, containing further error objects in this
        format to be displayed against this block's children
    """
    if hasattr(error, "as_json_data"):
        return error.as_json_data()
    else:
        return {"messages": error.messages}


def get_error_list_json_data(error_list):
    """
    Flatten an ErrorList instance containing any number of ValidationErrors
    (which may themselves contain multiple messages) into a list of error message strings.
    This does not consider any other properties of ValidationError other than `message`,
    so should not be used where ValidationError subclasses with nested block errors may be
    present.
    (In terms of StreamBlockValidationError et al: it's valid for use on non_block_errors
    but not block_errors)
    """
    return list(itertools.chain(*(err.messages for err in error_list.as_data())))


DECONSTRUCT_ALIASES = {
    Block: "wagtail.blocks.Block",
}
