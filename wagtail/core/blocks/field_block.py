import datetime

from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.forms.fields import CallableChoiceIterator
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from wagtail.core.rich_text import RichText
from wagtail.core.utils import resolve_model_string

from .base import Block


class FieldBlock(Block):
    """A block that wraps a Django form field"""

    def id_for_label(self, prefix):
        return self.field.widget.id_for_label(prefix)

    def render_form(self, value, prefix='', errors=None):
        field = self.field
        widget = field.widget

        widget_attrs = {'id': prefix, 'placeholder': self.label}

        field_value = field.prepare_value(self.value_for_form(value))

        if hasattr(widget, 'render_with_errors'):
            widget_html = widget.render_with_errors(prefix, field_value, attrs=widget_attrs, errors=errors)
            widget_has_rendered_errors = True
        else:
            widget_html = widget.render(prefix, field_value, attrs=widget_attrs)
            widget_has_rendered_errors = False

        return render_to_string('wagtailadmin/block_forms/field.html', {
            'name': self.name,
            'classes': self.meta.classname,
            'widget': widget_html,
            'field': field,
            'errors': errors if (not widget_has_rendered_errors) else None
        })

    def value_from_form(self, value):
        """
        The value that we get back from the form field might not be the type
        that this block works with natively; for example, the block may want to
        wrap a simple value such as a string in an object that provides a fancy
        HTML rendering (e.g. EmbedBlock).

        We therefore provide this method to perform any necessary conversion
        from the form field value to the block's native value. As standard,
        this returns the form field value unchanged.
        """
        return value

    def value_for_form(self, value):
        """
        Reverse of value_from_form; convert a value of this block's native value type
        to one that can be rendered by the form field
        """
        return value

    def value_from_datadict(self, data, files, prefix):
        return self.value_from_form(self.field.widget.value_from_datadict(data, files, prefix))

    def value_omitted_from_data(self, data, files, prefix):
        return self.field.widget.value_omitted_from_data(data, files, prefix)

    def clean(self, value):
        # We need an annoying value_for_form -> value_from_form round trip here to account for
        # the possibility that the form field is set up to validate a different value type to
        # the one this block works with natively
        return self.value_from_form(self.field.clean(self.value_for_form(value)))

    @property
    def media(self):
        return self.field.widget.media

    @property
    def required(self):
        # a FieldBlock is required if and only if its underlying form field is required
        return self.field.required

    class Meta:
        # No icon specified here, because that depends on the purpose that the
        # block is being used for. Feel encouraged to specify an icon in your
        # descendant block type
        icon = "placeholder"
        default = None


class CharBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, validators=(), **kwargs):
        # CharField's 'label' and 'initial' parameters are not exposed, as Block handles that functionality natively
        # (via 'label' and 'default')
        self.field = forms.CharField(
            required=required,
            help_text=help_text,
            max_length=max_length,
            min_length=min_length,
            validators=validators,
        )
        super().__init__(**kwargs)

    def get_searchable_content(self, value):
        return [force_text(value)]


class TextBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, rows=1, max_length=None, min_length=None, validators=(), **kwargs):
        self.field_options = {
            'required': required,
            'help_text': help_text,
            'max_length': max_length,
            'min_length': min_length,
            'validators': validators,
        }
        self.rows = rows
        super().__init__(**kwargs)

    @cached_property
    def field(self):
        from wagtail.admin.widgets import AdminAutoHeightTextInput
        field_kwargs = {'widget': AdminAutoHeightTextInput(attrs={'rows': self.rows})}
        field_kwargs.update(self.field_options)
        return forms.CharField(**field_kwargs)

    def get_searchable_content(self, value):
        return [force_text(value)]

    class Meta:
        icon = "pilcrow"


class BlockQuoteBlock(TextBlock):

    def render_basic(self, value, context=None):
        if value:
            return format_html('<blockquote>{0}</blockquote>', value)
        else:
            return ''

    class Meta:
        icon = "openquote"


class FloatBlock(FieldBlock):

    def __init__(self, required=True, max_value=None, min_value=None, validators=(), *args,
                 **kwargs):
        self.field = forms.FloatField(
            required=required,
            max_value=max_value,
            min_value=min_value,
            validators=validators,
        )
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "plus-inverse"


class DecimalBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, max_value=None, min_value=None,
                 max_digits=None, decimal_places=None, validators=(), *args, **kwargs):
        self.field = forms.DecimalField(
            required=required,
            help_text=help_text,
            max_value=max_value,
            min_value=min_value,
            max_digits=max_digits,
            decimal_places=decimal_places,
            validators=validators,
        )
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "plus-inverse"


class RegexBlock(FieldBlock):

    def __init__(self, regex, required=True, help_text=None, max_length=None, min_length=None,
                 error_messages=None, validators=(), *args, **kwargs):
        self.field = forms.RegexField(
            regex=regex,
            required=required,
            help_text=help_text,
            max_length=max_length,
            min_length=min_length,
            error_messages=error_messages,
            validators=validators,
        )
        super().__init__(*args, **kwargs)

    class Meta:
        icon = "code"


class URLBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, validators=(), **kwargs):
        self.field = forms.URLField(
            required=required,
            help_text=help_text,
            max_length=max_length,
            min_length=min_length,
            validators=validators,
        )
        super().__init__(**kwargs)

    class Meta:
        icon = "site"


class BooleanBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, **kwargs):
        # NOTE: As with forms.BooleanField, the default of required=True means that the checkbox
        # must be ticked to pass validation (i.e. it's equivalent to an "I agree to the terms and
        # conditions" box). To get the conventional yes/no behaviour, you must explicitly pass
        # required=False.
        self.field = forms.BooleanField(required=required, help_text=help_text)
        super().__init__(**kwargs)

    class Meta:
        icon = "tick-inverse"


class DateBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, format=None, validators=(), **kwargs):
        self.field_options = {
            'required': required,
            'help_text': help_text,
            'validators': validators,
        }
        try:
            self.field_options['input_formats'] = kwargs.pop('input_formats')
        except KeyError:
            pass
        self.format = format
        super().__init__(**kwargs)

    @cached_property
    def field(self):
        from wagtail.admin.widgets import AdminDateInput
        field_kwargs = {
            'widget': AdminDateInput(format=self.format),
        }
        field_kwargs.update(self.field_options)
        return forms.DateField(**field_kwargs)

    def to_python(self, value):
        # Serialising to JSON uses DjangoJSONEncoder, which converts date/time objects to strings.
        # The reverse does not happen on decoding, because there's no way to know which strings
        # should be decoded; we have to convert strings back to dates here instead.
        if value is None or isinstance(value, datetime.date):
            return value
        else:
            return parse_date(value)

    class Meta:
        icon = "date"


class TimeBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, validators=(), **kwargs):
        self.field_options = {
            'required': required,
            'help_text': help_text,
            'validators': validators
        }
        super().__init__(**kwargs)

    @cached_property
    def field(self):
        from wagtail.admin.widgets import AdminTimeInput
        field_kwargs = {'widget': AdminTimeInput}
        field_kwargs.update(self.field_options)
        return forms.TimeField(**field_kwargs)

    def to_python(self, value):
        if value is None or isinstance(value, datetime.time):
            return value
        else:
            return parse_time(value)

    class Meta:
        icon = "time"


class DateTimeBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, format=None, validators=(), **kwargs):
        self.field_options = {
            'required': required,
            'help_text': help_text,
            'validators': validators,
        }
        self.format = format
        super().__init__(**kwargs)

    @cached_property
    def field(self):
        from wagtail.admin.widgets import AdminDateTimeInput
        field_kwargs = {
            'widget': AdminDateTimeInput(format=self.format),
        }
        field_kwargs.update(self.field_options)
        return forms.DateTimeField(**field_kwargs)

    def to_python(self, value):
        if value is None or isinstance(value, datetime.datetime):
            return value
        else:
            return parse_datetime(value)

    class Meta:
        icon = "date"


class EmailBlock(FieldBlock):
    def __init__(self, required=True, help_text=None, validators=(), **kwargs):
        self.field = forms.EmailField(
            required=required,
            help_text=help_text,
            validators=validators,
        )
        super().__init__(**kwargs)

    class Meta:
        icon = "mail"


class IntegerBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, min_value=None,
                 max_value=None, validators=(), **kwargs):
        self.field = forms.IntegerField(
            required=required,
            help_text=help_text,
            min_value=min_value,
            max_value=max_value,
            validators=validators,
        )
        super().__init__(**kwargs)

    class Meta:
        icon = "plus-inverse"


class ChoiceBlock(FieldBlock):

    choices = ()

    def __init__(self, choices=None, default=None, required=True, help_text=None, validators=(), **kwargs):
        if choices is None:
            # no choices specified, so pick up the choice defined at the class level
            choices = self.choices

        if callable(choices):
            # Support of callable choices. Wrap the callable in an iterator so that we can
            # handle this consistently with ordinary choice lists;
            # however, the `choices` constructor kwarg as reported by deconstruct() should
            # remain as the callable
            choices_for_constructor = choices
            choices = CallableChoiceIterator(choices)
        else:
            # Cast as a list
            choices_for_constructor = choices = list(choices)

        # keep a copy of all kwargs (including our normalised choices list) for deconstruct()
        self._constructor_kwargs = kwargs.copy()
        self._constructor_kwargs['choices'] = choices_for_constructor
        if required is not True:
            self._constructor_kwargs['required'] = required
        if help_text is not None:
            self._constructor_kwargs['help_text'] = help_text

        # We will need to modify the choices list to insert a blank option, if there isn't
        # one already. We have to do this at render time in the case of callable choices - so rather
        # than having separate code paths for static vs dynamic lists, we'll _always_ pass a callable
        # to ChoiceField to perform this step at render time.

        # If we have a default choice and the field is required, we don't need to add a blank option.
        callable_choices = self.get_callable_choices(choices, blank_choice=not(default and required))

        self.field = forms.ChoiceField(
            choices=callable_choices,
            required=required,
            help_text=help_text,
            validators=validators,
        )
        super().__init__(default=default, **kwargs)

    def get_callable_choices(self, choices, blank_choice=True):
        """
        Return a callable that we can pass into `forms.ChoiceField`, which will provide the
        choices list with the addition of a blank choice (if blank_choice=True and one does not
        already exist).
        """
        def choices_callable():
            # Variable choices could be an instance of CallableChoiceIterator, which may be wrapping
            # something we don't want to evaluate multiple times (e.g. a database query). Cast as a
            # list now to prevent it getting evaluated twice (once while searching for a blank choice,
            # once while rendering the final ChoiceField).
            local_choices = list(choices)

            # If blank_choice=False has been specified, return the choices list as is
            if not blank_choice:
                return local_choices

            # Else: if choices does not already contain a blank option, insert one
            # (to match Django's own behaviour for modelfields:
            # https://github.com/django/django/blob/1.7.5/django/db/models/fields/__init__.py#L732-744)
            has_blank_choice = False
            for v1, v2 in local_choices:
                if isinstance(v2, (list, tuple)):
                    # this is a named group, and v2 is the value list
                    has_blank_choice = any([value in ('', None) for value, label in v2])
                    if has_blank_choice:
                        break
                else:
                    # this is an individual choice; v1 is the value
                    if v1 in ('', None):
                        has_blank_choice = True
                        break

            if not has_blank_choice:
                return BLANK_CHOICE_DASH + local_choices

            return local_choices
        return choices_callable

    def deconstruct(self):
        """
        Always deconstruct ChoiceBlock instances as if they were plain ChoiceBlocks with their
        choice list passed in the constructor, even if they are actually subclasses. This allows
        users to define subclasses of ChoiceBlock in their models.py, with specific choice lists
        passed in, without references to those classes ending up frozen into migrations.
        """
        return ('wagtail.core.blocks.ChoiceBlock', [], self._constructor_kwargs)

    def get_searchable_content(self, value):
        # Return the display value as the searchable value
        text_value = force_text(value)
        for k, v in self.field.choices:
            if isinstance(v, (list, tuple)):
                # This is an optgroup, so look inside the group for options
                for k2, v2 in v:
                    if value == k2 or text_value == force_text(k2):
                        return [force_text(k), force_text(v2)]
            else:
                if value == k or text_value == force_text(k):
                    return [force_text(v)]
        return []  # Value was not found in the list of choices

    class Meta:
        # No icon specified here, because that depends on the purpose that the
        # block is being used for. Feel encouraged to specify an icon in your
        # descendant block type
        icon = "placeholder"


class RichTextBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, editor='default', features=None, validators=(), **kwargs):
        self.field_options = {
            'required': required,
            'help_text': help_text,
            'validators': validators,
        }
        self.editor = editor
        self.features = features
        super().__init__(**kwargs)

    def get_default(self):
        if isinstance(self.meta.default, RichText):
            return self.meta.default
        else:
            return RichText(self.meta.default)

    def to_python(self, value):
        # convert a source-HTML string from the JSONish representation
        # to a RichText object
        return RichText(value)

    def get_prep_value(self, value):
        # convert a RichText object back to a source-HTML string to go into
        # the JSONish representation
        return value.source

    @cached_property
    def field(self):
        from wagtail.admin.rich_text import get_rich_text_editor_widget
        return forms.CharField(
            widget=get_rich_text_editor_widget(self.editor, features=self.features),
            **self.field_options
        )

    def value_for_form(self, value):
        # Rich text editors take the source-HTML string as input (and takes care
        # of expanding it for the purposes of the editor)
        return value.source

    def value_from_form(self, value):
        # Rich text editors return a source-HTML string; convert to a RichText object
        return RichText(value)

    def get_searchable_content(self, value):
        return [force_text(value.source)]

    class Meta:
        icon = "doc-full"


class RawHTMLBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, max_length=None, min_length=None, validators=(), **kwargs):
        self.field = forms.CharField(
            required=required, help_text=help_text, max_length=max_length, min_length=min_length,
            validators=validators,
            widget=forms.Textarea)
        super().__init__(**kwargs)

    def get_default(self):
        return mark_safe(self.meta.default or '')

    def to_python(self, value):
        return mark_safe(value)

    def get_prep_value(self, value):
        # explicitly convert to a plain string, just in case we're using some serialisation method
        # that doesn't cope with SafeText values correctly
        return str(value) + ''

    def value_for_form(self, value):
        # need to explicitly mark as unsafe, or it'll output unescaped HTML in the textarea
        return str(value) + ''

    def value_from_form(self, value):
        return mark_safe(value)

    class Meta:
        icon = 'code'


class ChooserBlock(FieldBlock):

    def __init__(self, required=True, help_text=None, validators=(), **kwargs):
        self._required = required
        self._help_text = help_text
        self._validators = validators
        super().__init__(**kwargs)

    """Abstract superclass for fields that implement a chooser interface (page, image, snippet etc)"""
    @cached_property
    def field(self):
        return forms.ModelChoiceField(
            queryset=self.target_model.objects.all(), widget=self.widget, required=self._required,
            validators=self._validators,
            help_text=self._help_text)

    def to_python(self, value):
        # the incoming serialised value should be None or an ID
        if value is None:
            return value
        else:
            try:
                return self.target_model.objects.get(pk=value)
            except self.target_model.DoesNotExist:
                return None

    def bulk_to_python(self, values):
        """Return the model instances for the given list of primary keys.

        The instances must be returned in the same order as the values and keep None values.
        """
        objects = self.target_model.objects.in_bulk(values)
        return [objects.get(id) for id in values]  # Keeps the ordering the same as in values.

    def get_prep_value(self, value):
        # the native value (a model instance or None) should serialise to a PK or None
        if value is None:
            return None
        else:
            return value.pk

    def value_from_form(self, value):
        # ModelChoiceField sometimes returns an ID, and sometimes an instance; we want the instance
        if value is None or isinstance(value, self.target_model):
            return value
        else:
            try:
                return self.target_model.objects.get(pk=value)
            except self.target_model.DoesNotExist:
                return None

    def clean(self, value):
        # ChooserBlock works natively with model instances as its 'value' type (because that's what you
        # want to work with when doing front-end templating), but ModelChoiceField.clean expects an ID
        # as the input value (and returns a model instance as the result). We don't want to bypass
        # ModelChoiceField.clean entirely (it might be doing relevant validation, such as checking page
        # type) so we convert our instance back to an ID here. It means we have a wasted round-trip to
        # the database when ModelChoiceField.clean promptly does its own lookup, but there's no easy way
        # around that...
        if isinstance(value, self.target_model):
            value = value.pk
        return super().clean(value)

    class Meta:
        # No icon specified here, because that depends on the purpose that the
        # block is being used for. Feel encouraged to specify an icon in your
        # descendant block type
        icon = "placeholder"


class PageChooserBlock(ChooserBlock):
    def __init__(self, page_type=None, can_choose_root=False, target_model=None, **kwargs):
        # We cannot simply deprecate 'target_model' in favour of 'page_type'
        # as it would force developers to update their old migrations.
        # Mapping the old 'target_model' to the new 'page_type' kwarg instead.
        if target_model:
            page_type = target_model

        if page_type:
            # Convert single string/model into a list
            if not isinstance(page_type, (list, tuple)):
                page_type = [page_type]
        else:
            page_type = []

        self.page_type = page_type
        self.can_choose_root = can_choose_root
        super().__init__(**kwargs)

    @cached_property
    def target_model(self):
        """
        Defines the model used by the base ChooserBlock for ID <-> instance
        conversions. If a single page type is specified in target_model,
        we can use that to get the more specific instance "for free"; otherwise
        use the generic Page model.
        """
        if len(self.target_models) == 1:
            return self.target_models[0]

        return resolve_model_string('wagtailcore.Page')

    @cached_property
    def target_models(self):
        target_models = []

        for target_model in self.page_type:
            target_models.append(
                resolve_model_string(target_model)
            )

        return target_models

    @cached_property
    def widget(self):
        from wagtail.admin.widgets import AdminPageChooser
        return AdminPageChooser(target_models=self.target_models,
                                can_choose_root=self.can_choose_root)

    def render_basic(self, value, context=None):
        if value:
            return format_html('<a href="{0}">{1}</a>', value.url, value.title)
        else:
            return ''

    def deconstruct(self):
        name, args, kwargs = super().deconstruct()

        if 'target_model' in kwargs or 'page_type' in kwargs:
            target_models = []

            for target_model in self.target_models:
                opts = target_model._meta
                target_models.append(
                    '{}.{}'.format(opts.app_label, opts.object_name)
                )

            kwargs.pop('target_model', None)
            kwargs['page_type'] = target_models

        return name, args, kwargs

    class Meta:
        icon = "redirect"


# Ensure that the blocks defined here get deconstructed as wagtailcore.blocks.FooBlock
# rather than wagtailcore.blocks.field.FooBlock
block_classes = [
    FieldBlock, CharBlock, URLBlock, RichTextBlock, RawHTMLBlock, ChooserBlock,
    PageChooserBlock, TextBlock, BooleanBlock, DateBlock, TimeBlock,
    DateTimeBlock, ChoiceBlock, EmailBlock, IntegerBlock, FloatBlock,
    DecimalBlock, RegexBlock, BlockQuoteBlock
]
DECONSTRUCT_ALIASES = {
    cls: 'wagtail.core.blocks.%s' % cls.__name__
    for cls in block_classes
}
__all__ = [cls.__name__ for cls in block_classes]
