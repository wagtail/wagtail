from __future__ import unicode_literals

import re
import collections

from django.core.exceptions import ValidationError
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.deconstruct import deconstructible
from django.utils.functional import cached_property
from django.template.loader import render_to_string
from django.forms import Media, CharField
from django.forms.utils import ErrorList

import six

# helpers for Javascript expression formatting

def indent(string, depth=1):
    """indent all non-empty lines of string by 'depth' 4-character tabs"""
    return re.sub(r'(^|\n)([^\n]+)', '\g<1>' + ('    ' * depth) + '\g<2>', string)

def js_dict(d):
    """
    Return a Javascript expression string for the dict 'd'.
    Keys are assumed to be strings consisting only of JS-safe characters, and will be quoted but not escaped;
    values are assumed to be valid Javascript expressions and will be neither escaped nor quoted (but will be
    wrapped in parentheses, in case some awkward git decides to use the comma operator...)
    """
    dict_items = [
        indent("'%s': (%s)" % (k, v))
        for (k, v) in d.items()
    ]
    return "{\n%s\n}" % ',\n'.join(dict_items)

# =========================================
# Top-level superclasses and helper objects
# =========================================

@deconstructible
class Block(object):
    creation_counter = 0

    """
    Setting a 'dependencies' list serves as a shortcut for the common case where a complex block type
    (such as struct, list or stream) relies on one or more inner block objects, and needs to ensure that
    the responses from the 'media' and 'html_declarations' include the relevant declarations for those inner
    blocks, as well as its own. Specifying these inner block objects in a 'dependencies' list means that
    the base 'media' and 'html_declarations' methods will return those declarations; the outer block type can
    then add its own declarations to the list by overriding those methods and using super().
    """
    dependencies = set()

    def all_blocks(self):
        """
        Return a set consisting of self and all block objects that are direct or indirect dependencies
        of this block
        """
        result = set([self])
        for dep in self.dependencies:
            result |= dep.all_blocks()
        return result

    def all_media(self):
        media = Media()
        for block in self.all_blocks():
            media += block.media
        return media

    def all_html_declarations(self):
        declarations = filter(bool, [block.html_declarations() for block in self.all_blocks()])
        return mark_safe('\n'.join(declarations))

    def __init__(self, **kwargs):
        if 'default' in kwargs:
            self.default = kwargs['default']  # if not specified, leave as the class-level default
        self.label = kwargs.get('label', None)

        # Increase the creation counter, and save our local copy.
        self.creation_counter = Block.creation_counter
        Block.creation_counter += 1
        self.definition_prefix = 'blockdef-%d' % self.creation_counter

    def set_name(self, name):
        self.name = name

        # if we don't have a label already, generate one from name
        if self.label is None:
            self.label = capfirst(name.replace('_', ' '))

    @property
    def media(self):
        return Media()

    def html_declarations(self):
        """
        Return an HTML fragment to be rendered on the form page once per block definition -
        as opposed to once per occurrence of the block. For example, the block definition
            ListBlock(label="Shopping list", TextInput(label="Product"))
        needs to output a <script type="text/template"></script> block containing the HTML for
        a 'product' text input, to that these can be dynamically added to the list. This
        template block must only occur once in the page, even if there are multiple 'shopping list'
        blocks on the page.

        Any element IDs used in this HTML fragment must begin with definition_prefix.
        (More precisely, they must either be definition_prefix itself, or begin with definition_prefix
        followed by a '-' character)
        """
        return ''

    def js_initializer(self):
        """
        Returns a Javascript expression string, or None if this block does not require any
        Javascript behaviour. This expression evaluates to an initializer function, a function that
        takes the ID prefix and applies JS behaviour to the block instance with that value and prefix.

        The parent block of this block (or the top-level page code) must ensure that this
        expression is not evaluated more than once. (The resulting initializer function can and will be
        called as many times as there are instances of this block, though.)
        """
        return None

    def render_form(self, value, prefix=''):
        """
        Render the HTML for this block with 'value' as its content.
        """
        raise NotImplementedError('%s.render_form' % self.__class__)

    def value_from_datadict(self, data, files, prefix):
        raise NotImplementedError('%s.value_from_datadict' % self.__class__)

    def bind(self, value, prefix=None, error=None):
        """
        Return a BoundBlock which represents the association of this block definition with a value
        and a prefix (and optionally, a ValidationError to be rendered).
        BoundBlock primarily exists as a convenience to allow rendering within templates:
        bound_block.render() rather than blockdef.render(value, prefix) which can't be called from
        within a template.
        """
        return BoundBlock(self, value, prefix=prefix, error=error)

    def prototype_block(self):
        """
        Return a BoundBlock that can be used as a basis for new empty block instances to be added on the fly
        (new list items, for example). This will have a prefix of '__PREFIX__' (to be dynamically replaced with
        a real prefix when it's inserted into the page) and a value equal to the block's default value.
        """
        return self.bind(self.default, '__PREFIX__')

    def clean(self, value):
        """
        Validate value and return a cleaned version of it, or throw a ValidationError if validation fails.
        The thrown ValidationError instance will subsequently be passed to render() to display the
        error message; nested blocks therefore need to wrap child validations like this:
        https://docs.djangoproject.com/en/dev/ref/forms/validation/#raising-multiple-errors

        NB The ValidationError must have an error_list property (which can be achieved by passing a
        list or an individual error message to its constructor), NOT an error_dict -
        Django has problems nesting ValidationErrors with error_dicts.
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
        """
        return value

    def get_prep_value(self, value):
        """
        The reverse of to_python; convert the python value into JSON-serialisable form.
        """
        return value

    def render(self, value):
        """
        Return a text rendering of 'value', suitable for display on templates.
        """
        return force_text(value)


class BoundBlock(object):
    def __init__(self, block, value, prefix=None, error=None):
        self.block = block
        self.value = value
        self.prefix = prefix
        self.error = error

    def render_form(self):
        return self.block.render_form(self.value, self.prefix, error=self.error)

    def render(self):
        return self.block.render(self.value)


# ==========
# Text input
# ==========

class TextInputBlock(Block):
    default = ''

    def render_form(self, value, prefix='', error=None):
        if self.label:
            return format_html(
                """<label for="{prefix}">{label}</label> <input type="text" name="{prefix}" id="{prefix}" value="{value}">""",
                prefix=prefix, label=self.label, value=value
            )
        else:
            return format_html(
                """<input type="text" name="{prefix}" id="{prefix}" value="{value}">""",
                prefix=prefix, label=self.label, value=value
            )

    def value_from_datadict(self, data, files, prefix):
        return data.get(prefix, '')


# ===========
# Field block
# ===========

# FIXME: form field instances are not deconstructible for migrations. Need some other way to refer to
# them in the initialiser, in the case that FieldBlock appears inline within a StreamField definition.
# (Referring to them by class would probably work; it's unlikely that any parameter passed to them
# would affect anything you're doing in migrations)

class FieldBlock(Block):
    default = None

    def __init__(self, field, **kwargs):
        super(FieldBlock, self).__init__(**kwargs)
        self.field = field

    def render_form(self, value, prefix='', error=None):
        widget = self.field.widget

        widget_html = widget.render(prefix, value, {'id': prefix})

        #if error:
        #    error_html = str(ErrorList(error.error_list))
        #else:
        #    error_html = ''

        if self.label:
            label_html = format_html(
                """<label for={label_id}>{label}</label> """,
                label_id=widget.id_for_label(prefix), label=self.label
            )
        else:
            label_html = ''

        return render_to_string('wagtailadmin/block_forms/field.html', {
            'widget': widget_html,
            'label_tag': label_html,
            'field': self.field,
            'errors': error.error_list if error else [],  # TODO: should this be ErrorList(error.error_list)?
        })

    def value_from_datadict(self, data, files, prefix):
        return self.field.widget.value_from_datadict(data, files, prefix)

    def clean(self, value):
        return self.field.clean(value)

class HeadingBlock(FieldBlock):
    def __init__(self, tag_name='h1', **kwargs):
        self.tag_name = tag_name
        super(HeadingBlock, self).__init__(CharField(), **kwargs)

    def render(self, value):
        return format_html("<{tag}>{value}</{tag}>", tag=self.tag_name, value=value)

# =======
# Chooser
# =======

class ChooserBlock(Block):
    default = None

    @property
    def media(self):
        return Media(js=['wagtailadmin/js/blocks/chooser.js'])

    def js_initializer(self):
        return "Chooser('%s')" % self.definition_prefix

    def render_form(self, value, prefix='', error=None):
        if self.label:
            return format_html(
                """<label>{label}</label> <input type="button" id="{prefix}-button" value="Choose a thing">""",
                label=self.label, prefix=prefix
            )
        else:
            return format_html(
                """<input type="button" id="{prefix}-button" value="Choose a thing">""",
                prefix=prefix
            )

    def value_from_datadict(self, data, files, prefix):
        return 123


# ===========
# StructBlock
# ===========

class BaseStructBlock(Block):
    default = {}
    template = "wagtailadmin/blocks/struct.html"

    def __init__(self, local_blocks=None, **kwargs):
        super(BaseStructBlock, self).__init__(**kwargs)

        self.child_blocks = self.base_blocks.copy()  # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self.child_blocks[name] = block

        self.child_js_initializers = {}
        for name, block in self.child_blocks.items():
            js_initializer = block.js_initializer()
            if js_initializer is not None:
                self.child_js_initializers[name] = js_initializer

        self.dependencies = set(self.child_blocks.values())

    def js_initializer(self):
        # skip JS setup entirely if no children have js_initializers
        if not self.child_js_initializers:
            return None

        return "StructBlock(%s)" % js_dict(self.child_js_initializers)

    @property
    def media(self):
        return Media(js=['wagtailadmin/js/blocks/struct.js'])

    def render_form(self, value, prefix='', error=None):
        child_renderings = [
            block.render_form(value.get(name, block.default), prefix="%s-%s" % (prefix, name),
                error=error.params.get(name) if error else None)
            for name, block in self.child_blocks.items()
        ]

        list_items = format_html_join('\n', "<li>{0}</li>", [
            [child_rendering]
            for child_rendering in child_renderings
        ])

       
        # Can these be rendered with a template?
        if self.label:
            return format_html('<div class="struct-block"><label>{0}</label> <ul>{1}</ul></div>', self.label, list_items)
        else:
            return format_html('<div class="struct-block"><ul>{0}</ul></div>', list_items)

    def value_from_datadict(self, data, files, prefix):
        return dict([
            (name, block.value_from_datadict(data, files, '%s-%s' % (prefix, name)))
            for name, block in self.child_blocks.items()
        ])

    def clean(self, value):
        result = {}
        errors = {}
        for name, val in value.items():
            try:
                result[name] = self.child_blocks[name].clean(val)
            except ValidationError as e:
                errors[name] = e

        if errors:
            # The message here is arbitrary - outputting error messages is delegated to the child blocks,
            # which only involves the 'params' dict
            raise ValidationError('Validation error in StructBlock', params=errors)

        return result

    def to_python(self, value):
        # recursively call to_python on children and return as a StructValue
        return StructValue(self, [
            (
                name,
                child_block.to_python(value.get(name, child_block.default))
            )
            for name, child_block in self.child_blocks.items()
        ])

    def get_prep_value(self, value):
        # recursively call get_prep_value on children and return as a plain dict
        return dict([
            (name, self.child_blocks[name].get_prep_value(val))
            for name, val in value.items()
        ])

    def render(self, value):
        return render_to_string(self.template, {'self': value})

@python_2_unicode_compatible  # ensures that the output of __str__ doesn't lose its 'safe' flag
class StructValue(collections.OrderedDict):
    def __init__(self, block, *args):
        super(StructValue, self).__init__(*args)
        self.block = block

    def __str__(self):
        return self.block.render(self)


class DeclarativeSubBlocksMetaclass(type):
    """
    Metaclass that collects sub-blocks declared on the base classes.
    (cheerfully stolen from https://github.com/django/django/blob/master/django/forms/forms.py)
    """
    def __new__(mcs, name, bases, attrs):
        # Collect sub-blocks from current class.
        current_blocks = []
        for key, value in list(attrs.items()):
            if isinstance(value, Block):
                current_blocks.append((key, value))
                value.set_name(key)
                attrs.pop(key)
        current_blocks.sort(key=lambda x: x[1].creation_counter)
        attrs['declared_blocks'] = collections.OrderedDict(current_blocks)

        new_class = (super(DeclarativeSubBlocksMetaclass, mcs)
            .__new__(mcs, name, bases, attrs))

        # Walk through the MRO.
        declared_blocks = collections.OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect sub-blocks from base class.
            if hasattr(base, 'declared_blocks'):
                declared_blocks.update(base.declared_blocks)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_blocks:
                    declared_blocks.pop(attr)

        new_class.base_blocks = declared_blocks
        new_class.declared_blocks = declared_blocks

        return new_class

class StructBlock(six.with_metaclass(DeclarativeSubBlocksMetaclass, BaseStructBlock)):
    pass


# =========
# ListBlock
# =========

class ListBlock(Block):
    default = []

    def __init__(self, child_block, **kwargs):
        super(ListBlock, self).__init__(**kwargs)

        if isinstance(child_block, type):
            # child_block was passed as a class, so convert it to a block instance
            self.child_block = child_block()
        else:
            self.child_block = child_block

        self.dependencies = set([self.child_block])
        self.child_js_initializer = self.child_block.js_initializer()

    @property
    def media(self):
        return Media(js=['wagtailadmin/js/blocks/sequence.js', 'wagtailadmin/js/blocks/list.js'])

    def render_list_member(self, value, prefix, index, error=None):
        """
        Render the HTML for a single list item in the form. This consists of an <li> wrapper, hidden fields
        to manage ID/deleted state, delete/reorder buttons, and the child block's own form HTML.
        """
        child = self.child_block.bind(value, prefix="%s-value" % prefix, error=error)
        return render_to_string('wagtailadmin/block_forms/list_member.html', {
            'prefix': prefix,
            'child': child,
            'index': index,
        })

    def html_declarations(self):
        # generate the HTML to be used when adding a new item to the list;
        # this is the output of render_list_member as rendered with the prefix '__PREFIX__'
        # (to be replaced dynamically when adding the new item) and the child block's default value
        # as its value.
        list_member_html = self.render_list_member(self.child_block.default, '__PREFIX__', '')

        return format_html(
            '<script type="text/template" id="{0}-newmember">{1}</script>',
            self.definition_prefix, list_member_html
        )

    def js_initializer(self):
        opts = {'definitionPrefix': "'%s'" % self.definition_prefix}

        if self.child_js_initializer:
            opts['childInitializer'] = self.child_js_initializer

        return "ListBlock(%s)" % js_dict(opts)

    def render_form(self, value, prefix='', error=None):
        list_members_html = [
            self.render_list_member(child_val, "%s-%d" % (prefix, i), i,
                error=error.params[i] if error else None)
            for (i, child_val) in enumerate(value)
        ]

        return render_to_string('wagtailadmin/block_forms/list.html', {
            'label': self.label,
            'prefix': prefix,
            'list_members_html': list_members_html,
        })

    def value_from_datadict(self, data, files, prefix):
        count = int(data['%s-count' % prefix])
        values_with_indexes = []
        for i in range(0, count):
            if data['%s-%d-deleted' % (prefix, i)]:
                continue
            values_with_indexes.append(
                (
                    data['%s-%d-order' % (prefix, i)],
                    self.child_block.value_from_datadict(data, files, '%s-%d-value' % (prefix, i))
                )
            )

        values_with_indexes.sort()
        return [v for (i, v) in values_with_indexes]

    def clean(self, value):
        result = []
        errors = []
        for child_val in value:
            try:
                result.append(self.child_block.clean(child_val))
            except ValidationError as e:
                errors.append(e)
            else:
                errors.append(None)

        if any(errors):
            # The message here is arbitrary - outputting error messages is delegated to the child blocks,
            # which only involves the 'params' list
            raise ValidationError('Validation error in ListBlock', params=errors)

        return result

    def to_python(self, value):
        # recursively call to_python on children and return as a list
        return [
            self.child_block.to_python(item)
            for item in value
        ]

    def get_prep_value(self, value):
        # recursively call get_prep_value on children and return as a list
        return [
            self.child_block.get_prep_value(item)
            for item in value
        ]


# ===========
# StreamBlock
# ===========

class BaseStreamBlock(Block):
    default = []

    def __init__(self, local_blocks=None, **kwargs):
        super(BaseStreamBlock, self).__init__(**kwargs)

        self.child_blocks = self.base_blocks.copy()  # create a local (shallow) copy of base_blocks so that it can be supplemented by local_blocks
        if local_blocks:
            for name, block in local_blocks:
                block.set_name(name)
                self.child_blocks[name] = block

        self.dependencies = set(self.child_blocks.values())

    def render_list_member(self, block_type_name, value, prefix, index, error=None):
        """
        Render the HTML for a single list item. This consists of an <li> wrapper, hidden fields
        to manage ID/deleted state/type, delete/reorder buttons, and the child block's own HTML.
        """
        child_block = self.child_blocks[block_type_name]
        child = child_block.bind(value, prefix="%s-value" % prefix, error=error)
        return render_to_string('wagtailadmin/block_forms/stream_member.html', {
            'child_blocks': self.child_blocks.values(),
            'block_type_name': block_type_name,
            'prefix': prefix,
            'child': child,
            'index': index,
        })

    def html_declarations(self):
        return format_html_join(
            '\n', '<script type="text/template" id="{0}-newmember-{1}">{2}</script>',
            [
                (
                    self.definition_prefix,
                    name,
                    self.render_list_member(name, child_block.default, '__PREFIX__', '')
                )
                for name, child_block in self.child_blocks.items()
            ]
        )

    @property
    def media(self):
        return Media(js=['wagtailadmin/js/blocks/sequence.js', 'wagtailadmin/js/blocks/stream.js'])

    def js_initializer(self):
        # compile a list of info dictionaries, one for each available block type
        child_blocks = []
        for name, child_block in self.child_blocks.items():
            # each info dictionary specifies at least a block name
            child_block_info = {'name': "'%s'" % name}

            # if the child defines a JS initializer function, include that in the info dict
            # along with the param that needs to be passed to it for initializing an empty/default block
            # of that type
            child_js_initializer = child_block.js_initializer()
            if child_js_initializer:
                child_block_info['initializer'] = child_js_initializer

            child_blocks.append(indent(js_dict(child_block_info)))

        opts = {
            'definitionPrefix': "'%s'" % self.definition_prefix,
            'childBlocks': '[\n%s\n]' % ',\n'.join(child_blocks),
        }

        return "StreamBlock(%s)" % js_dict(opts)

    def render_form(self, value, prefix='', error=None):
        list_members_html = [
            self.render_list_member(block_type, child_value, "%s-%d" % (prefix, i), i,
                error=error.params[i] if error else None)
            for (i, (child_value, block_type)) in enumerate(value.values_with_types)
        ]

        return render_to_string('wagtailadmin/block_forms/stream.html', {
            'label': self.label,
            'prefix': prefix,
            'list_members_html': list_members_html,
            'child_blocks': self.child_blocks.values(),
            'header_menu_prefix': '%s-before' % prefix,
        })

    def value_from_datadict(self, data, files, prefix):
        count = int(data['%s-count' % prefix])
        values_with_indexes = []
        for i in range(0, count):
            if data['%s-%d-deleted' % (prefix, i)]:
                continue
            block_type_name = data['%s-%d-type' % (prefix, i)]
            child_block = self.child_blocks[block_type_name]

            values_with_indexes.append(
                (
                    data['%s-%d-order' % (prefix, i)],
                    child_block.value_from_datadict(data, files, '%s-%d-value' % (prefix, i)),
                    block_type_name,
                )
            )

        values_with_indexes.sort()
        return StreamValue(self, [(val, typ) for (index, val, typ) in values_with_indexes])

    def clean(self, value):
        result = []
        errors = []
        for child_type, child_val in value.values_with_types:
            child_block = self.child_blocks[child_type]
            try:
                result.append(
                    (child_block.clean(child_val), child_type)
                )
            except ValidationError as e:
                errors.append(e)
            else:
                errors.append(None)

        if any(errors):
            # The message here is arbitrary - outputting error messages is delegated to the child blocks,
            # which only involves the 'params' list
            raise ValidationError('Validation error in StreamBlock', params=errors)

        return StreamValue(self, result)

    def to_python(self, value):
        # the incoming JSONish representation is a list of dicts, each with a 'type' and 'value' field.
        # Convert this to a StreamValue backed by a list of (value, type) tuples
        return StreamValue(self, [
            (self.child_blocks[item['type']].to_python(item['value']), item['type'])
            for item in value
        ])

    def get_prep_value(self, value):
        return [
            {'type': bound_block.block.name, 'value': bound_block.block.get_prep_value(bound_block.value)}
            for bound_block in value.bound_blocks
        ]

    def render(self, value):
        return format_html_join('\n', '<div class="block-{1}">{0}</div>',
            [(bound_block.render(), bound_block.block.name) for bound_block in value.bound_blocks]
        )


class StreamBlock(six.with_metaclass(DeclarativeSubBlocksMetaclass, BaseStreamBlock)):
    pass


@python_2_unicode_compatible
class StreamValue(collections.Sequence):
    """
    Custom type used to represent the value of a StreamBlock; behaves as a sequence of block values
    so that we can naturally iterate over it in template code, but also allows retrieval of
    (value, type) tuples as required for the form (and other complex rendering logic) to work.
    """
    def __init__(self, stream_block, values_with_types):
        self.stream_block = stream_block
        self.values_with_types = values_with_types

    def __getitem__(self, i):
        return self.values_with_types[i][0]

    def __len__(self):
        return len(self.values_with_types)

    def __repr__(self):
        return repr(list(self))

    def __str__(self):
        return self.stream_block.render(self)

    @cached_property
    def bound_blocks(self):
        return [
            BoundBlock(self.stream_block.child_blocks[block_type], value)
            for value, block_type in self.values_with_types
        ]
