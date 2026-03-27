from wagtail.admin.viewsets.base import ViewSet


class ListingViewSetMixin:
    #: The number of items to display per page in the index view.
    list_per_page = ViewSet.UNDEFINED

    #: The default ordering to use for the index view.
    #: Can be a string or a list/tuple in the same format as Django's
    #: :attr:`~django.db.models.Options.ordering`.
    ordering = ViewSet.UNDEFINED

    list_display = ViewSet.UNDEFINED
    """
    A list or tuple, where each item is either:

    - The name of a field on the model;
    - The name of a callable or property on the model that accepts a single
      parameter for the model instance; or
    - An instance of the ``wagtail.admin.ui.tables.Column`` class.

    If the name refers to a database field, the ability to sort the listing
    by the database column will be offered and the field's verbose name
    will be used as the column header.

    If the name refers to a callable or property, an ``admin_order_field``
    attribute can be defined on it to point to the database column for
    sorting. A ``short_description`` attribute can also be defined on the
    callable or property to be used as the column header.
    """

    list_filter = ViewSet.UNDEFINED
    """
    A list or tuple, where each item is the name of model fields of type
    ``BooleanField``, ``CharField``, ``DateField``, ``DateTimeField``,
    ``IntegerField`` or ``ForeignKey``.
    Alternatively, it can also be a dictionary that maps a field name to a
    list of lookup expressions.
    This will be passed as django-filter's ``FilterSet.Meta.fields``
    attribute. See
    `its documentation <https://django-filter.readthedocs.io/en/stable/guide/usage.html#generating-filters-with-meta-fields>`_
    for more details.
    If ``filterset_class`` is set, this attribute will be ignored.
    """

    filterset_class = ViewSet.UNDEFINED
    """
    A subclass of ``wagtail.admin.filters.WagtailFilterSet``, which is a
    subclass of `django_filters.FilterSet <https://django-filter.readthedocs.io/en/stable/ref/filterset.html>`_.
    This will be passed to the ``filterset_class`` attribute of the index view.
    """

    list_export = ViewSet.UNDEFINED
    """
    A list or tuple, where each item is the name of a field, an attribute,
    or a single-argument callable on the model to be exported.
    """

    export_headings = ViewSet.UNDEFINED
    """
    A dictionary of export column heading overrides in the format
    ``{field_name: heading}``.
    """

    export_filename = ViewSet.UNDEFINED
    """The base file name for the exported listing, without extensions."""

    def get_index_view_kwargs(self, **kwargs):
        view_kwargs = {
            "paginate_by": self.list_per_page,
            "default_ordering": self.ordering,
            "list_display": self.list_display,
            "list_filter": self.list_filter,
            "list_export": self.list_export,
            "export_headings": self.export_headings,
            "export_filename": self.export_filename,
            "filterset_class": self.filterset_class,
            **kwargs,
        }
        return view_kwargs
