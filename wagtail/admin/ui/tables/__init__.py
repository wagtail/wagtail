"""Helper classes for formatting data as tables"""

from collections import OrderedDict
from collections.abc import Mapping

from django.contrib.admin.utils import quote
from django.forms import MediaDefiningClass
from django.template.loader import get_template
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext, gettext_lazy

from wagtail.admin.ui.components import Component
from wagtail.coreutils import multigetattr


class BaseColumn(metaclass=MediaDefiningClass):
    class Header:
        # Helper object used for rendering column headers in templates -
        # behaves as a component (i.e. it has a render_html method) but delegates rendering
        # to Column.render_header_html
        def __init__(self, column):
            self.column = column

        def render_html(self, parent_context):
            return self.column.render_header_html(parent_context)

    class Cell:
        # Helper object used for rendering table cells in templates -
        # behaves as a component (i.e. it has a render_html method) but delegates rendering
        # to Column.render_cell_html
        def __init__(self, column, instance):
            self.column = column
            self.instance = instance

        def render_html(self, parent_context):
            return self.column.render_cell_html(self.instance, parent_context)

    header_template_name = "wagtailadmin/tables/column_header.html"
    cell_template_name = None

    def __init__(
        self,
        name,
        label=None,
        accessor=None,
        classname=None,
        sort_key=None,
        width=None,
        ascending_title_text=None,
        descending_title_text=None,
    ):
        self.name = name
        self.accessor = accessor or name
        if label is None:
            self.label = capfirst(name.replace("_", " "))
        else:
            self.label = label
        self.classname = classname
        self.sort_key = sort_key
        self.header = Column.Header(self)
        self.width = width
        self.ascending_title_text = ascending_title_text
        self.descending_title_text = descending_title_text

    def get_header_context_data(self, parent_context):
        """
        Compiles the context dictionary to pass to the header template when rendering the column header
        """
        table = parent_context["table"]
        return {
            "column": self,
            "table": table,
            "is_orderable": bool(self.sort_key),
            "is_ascending": self.sort_key and table.ordering == self.sort_key,
            "is_descending": self.sort_key and table.ordering == ("-" + self.sort_key),
            "request": parent_context.get("request"),
            "ascending_title_text": self.ascending_title_text
            or table.get_ascending_title_text(self),
            "descending_title_text": self.descending_title_text
            or table.get_descending_title_text(self),
        }

    @cached_property
    def header_template(self):
        return get_template(self.header_template_name)

    @cached_property
    def cell_template(self):
        if self.cell_template_name is None:
            raise NotImplementedError(
                "cell_template_name must be specified on %r" % self
            )
        return get_template(self.cell_template_name)

    def render_header_html(self, parent_context):
        """
        Renders the column's header
        """
        context = self.get_header_context_data(parent_context)
        return self.header_template.render(context)

    def get_cell_context_data(self, instance, parent_context):
        """
        Compiles the context dictionary to pass to the cell template when rendering a table cell for
        the given instance
        """
        return {
            "instance": instance,
            "column": self,
            "row": parent_context["row"],
            "table": parent_context["table"],
            "request": parent_context.get("request"),
        }

    def render_cell_html(self, instance, parent_context):
        """
        Renders a table cell containing data for the given instance
        """
        context = self.get_cell_context_data(instance, parent_context)
        return self.cell_template.render(context)

    def get_cell(self, instance):
        """
        Return an object encapsulating this column and an item of data, which we can use for
        rendering a table cell into a template
        """
        return Column.Cell(self, instance)

    def __repr__(self):
        return "<{}.{}: {}>".format(
            self.__class__.__module__,
            self.__class__.__qualname__,
            self.name,
        )


class Column(BaseColumn):
    """A column that displays a single field of data from the model"""

    cell_template_name = "wagtailadmin/tables/cell.html"

    def get_value(self, instance):
        """
        Given an instance (i.e. any object containing data), extract the field of data to be
        displayed in a cell of this column
        """
        if callable(self.accessor):
            return self.accessor(instance)
        else:
            return multigetattr(instance, self.accessor)

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["value"] = self.get_value(instance)
        return context


class ButtonsColumnMixin:
    """A mixin for columns that contain buttons"""

    buttons = []

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["buttons"] = sorted(self.get_buttons(instance, parent_context))
        return context

    def get_buttons(self, instance, parent_context):
        return self.buttons


class TitleColumn(Column):
    """A column where data is styled as a title and wrapped in a link or <label>"""

    cell_template_name = "wagtailadmin/tables/title_cell.html"

    def __init__(
        self,
        name,
        url_name=None,
        get_url=None,
        label_prefix=None,
        get_label_id=None,
        link_classname=None,
        link_attrs=None,
        id_accessor="pk",
        **kwargs,
    ):
        super().__init__(name, **kwargs)
        self.url_name = url_name
        self._get_url_func = get_url
        self.label_prefix = label_prefix
        self._get_label_id_func = get_label_id
        self.link_attrs = link_attrs or {}
        self.link_classname = link_classname
        self.id_accessor = id_accessor

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["link_attrs"] = self.get_link_attrs(instance, parent_context)
        context["link_attrs"]["href"] = context["link_url"] = self.get_link_url(
            instance, parent_context
        )
        if self.link_classname is not None:
            context["link_attrs"]["class"] = self.link_classname
        context["label_id"] = self.get_label_id(instance, parent_context)
        return context

    def get_link_attrs(self, instance, parent_context):
        return self.link_attrs.copy()

    def get_link_url(self, instance, parent_context):
        if self._get_url_func:
            return self._get_url_func(instance)
        elif self.url_name:
            id = multigetattr(instance, self.id_accessor)
            return reverse(self.url_name, args=(quote(id),))

    def get_label_id(self, instance, parent_context):
        if self._get_label_id_func:
            return self._get_label_id_func(instance)
        elif self.label_prefix:
            id = multigetattr(instance, self.id_accessor)
            return f"{self.label_prefix}-{id}"


class StatusFlagColumn(Column):
    """Represents a boolean value as a status tag (or lack thereof, if the corresponding label is None)"""

    cell_template_name = "wagtailadmin/tables/status_flag_cell.html"

    def __init__(self, name, true_label=None, false_label=None, **kwargs):
        super().__init__(name, **kwargs)
        self.true_label = true_label
        self.false_label = false_label


class StatusTagColumn(Column):
    """Represents a status tag"""

    cell_template_name = "wagtailadmin/tables/status_tag_cell.html"

    def __init__(self, name, primary=None, **kwargs):
        super().__init__(name, **kwargs)
        self.primary = primary

    def get_primary(self, instance):
        if callable(self.primary):
            return self.primary(instance)
        return self.primary

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["primary"] = self.get_primary(instance)
        return context


class BooleanColumn(Column):
    """Represents a True/False/None value as a tick/cross/question icon"""

    cell_template_name = "wagtailadmin/tables/boolean_cell.html"


class LiveStatusTagColumn(StatusTagColumn):
    """Represents a live/draft status tag"""

    def __init__(self, **kwargs):
        super().__init__(
            "status_string",
            label=kwargs.pop("label", gettext("Status")),
            sort_key=kwargs.pop("sort_key", "live"),
            primary=lambda instance: instance.live,
            **kwargs,
        )


class DateColumn(Column):
    """Outputs a date in human-readable format"""

    cell_template_name = "wagtailadmin/tables/date_cell.html"


class UpdatedAtColumn(DateColumn):
    """Outputs the _updated_at date annotation in human-readable format"""

    def __init__(self, **kwargs):
        super().__init__(
            "_updated_at",
            label=kwargs.pop("label", gettext("Updated")),
            sort_key=kwargs.pop("sort_key", "_updated_at"),
            **kwargs,
        )


class UserColumn(Column):
    """Outputs the username and avatar for a user"""

    cell_template_name = "wagtailadmin/tables/user_cell.html"

    def __init__(self, name, blank_display_name="", **kwargs):
        super().__init__(name, **kwargs)
        self.blank_display_name = blank_display_name

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)

        user = context["value"]
        if user:
            try:
                full_name = user.get_full_name().strip()
            except AttributeError:
                full_name = ""
            context["display_name"] = full_name or user.get_username()
        else:
            context["display_name"] = self.blank_display_name
        return context


class BulkActionsCheckboxColumn(BaseColumn):
    header_template_name = "wagtailadmin/bulk_actions/select_all_checkbox_cell.html"
    cell_template_name = "wagtailadmin/bulk_actions/listing_checkbox_cell.html"

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["obj"] = instance
        return context


class ReferencesColumn(Column):
    cell_template_name = "wagtailadmin/tables/references_cell.html"

    def __init__(
        self,
        name,
        label=None,
        accessor=None,
        classname=None,
        sort_key=None,
        width=None,
        get_url=None,
        describe_on_delete=False,
    ):
        super().__init__(name, label, accessor, classname, sort_key, width)
        self._get_url_func = get_url
        self.describe_on_delete = describe_on_delete

    def get_edit_url(self, instance):
        if self._get_url_func:
            return self._get_url_func(instance)

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["edit_url"] = self.get_edit_url(instance)
        context["describe_on_delete"] = self.describe_on_delete
        return context


class Table(Component):
    template_name = "wagtailadmin/tables/table.html"
    classname = "listing"
    header_row_classname = ""
    ascending_title_text_format = gettext_lazy(
        "Sort by '%(label)s' in ascending order."
    )
    descending_title_text_format = gettext_lazy(
        "Sort by '%(label)s' in descending order."
    )

    def __init__(
        self,
        columns,
        data,
        template_name=None,
        base_url=None,
        ordering=None,
        classname=None,
        attrs=None,
    ):
        self.columns = OrderedDict([(column.name, column) for column in columns])
        self.data = data
        if template_name:
            self.template_name = template_name
        self.base_url = base_url
        self.ordering = ordering
        if classname is not None:
            self.classname = classname
        self.base_attrs = attrs or {}

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["table"] = self
        context["request"] = parent_context.get("request")
        return context

    @property
    def media(self):
        media = super().media
        for col in self.columns.values():
            media += col.media
        return media

    @property
    def rows(self):
        for index, instance in enumerate(self.data):
            yield Table.Row(self, instance, index)

    @property
    def row_count(self):
        return len(self.data)

    @property
    def attrs(self):
        attrs = self.base_attrs.copy()
        attrs["class"] = self.classname
        return attrs

    def get_row_classname(self, instance):
        return ""

    def get_row_attrs(self, instance):
        attrs = {}
        classname = self.get_row_classname(instance)
        if classname:
            attrs["class"] = classname
        return attrs

    def has_column_widths(self):
        return any(column.width for column in self.columns.values())

    def get_ascending_title_text(self, column):
        if self.ascending_title_text_format:
            return self.ascending_title_text_format % {"label": column.label}

    def get_descending_title_text(self, column):
        if self.descending_title_text_format:
            return self.descending_title_text_format % {"label": column.label}

    class Row(Mapping):
        # behaves as an OrderedDict whose items are the rendered results of
        # the corresponding column's format_cell method applied to the instance
        def __init__(self, table, instance, index):
            self.table = table
            self.columns = table.columns
            self.instance = instance
            self.index = index

        def __len__(self):
            return len(self.columns)

        def __getitem__(self, key):
            return self.columns[key].get_cell(self.instance)

        def __iter__(self):
            yield from self.columns

        def __repr__(self):
            return repr([col.get_cell(self.instance) for col in self.columns.values()])

        @cached_property
        def classname(self):
            return self.table.get_row_classname(self.instance)

        @cached_property
        def attrs(self):
            return self.table.get_row_attrs(self.instance)


class InlineActionsTable(Table):
    classname = "listing listing--inline-actions"
