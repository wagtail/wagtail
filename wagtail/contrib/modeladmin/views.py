from __future__ import absolute_import, unicode_literals

import operator
import sys
import warnings
from collections import OrderedDict
from functools import reduce

from django import forms
from django.contrib.admin import FieldListFilter, widgets
from django.contrib.admin.exceptions import DisallowedModelAdminLookup
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.utils import (
    get_fields_from_path, lookup_needs_distinct, prepare_lookup_value, quote, unquote)
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, SuspiciousOperation
from django.core.paginator import InvalidPage, Paginator
from django.db import models
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel, ManyToManyField
from django.db.models.sql.constants import QUERY_TERMS
from django.shortcuts import redirect
from django.template.defaultfilters import filesizeformat
from django.utils import six
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView

from wagtail.utils.deprecation import RemovedInWagtail112Warning
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class)

from .forms import ParentChooserForm


class WMABaseView(TemplateView):
    """
    Groups together common functionality for all app views.
    """
    model_admin = None
    meta_title = ''
    page_title = ''
    page_subtitle = ''

    def __init__(self, model_admin, **kwargs):
        super(WMABaseView, self).__init__(**kwargs)
        self.model_admin = model_admin
        self.model = model_admin.model
        self.opts = self.model._meta
        self.app_label = force_text(self.opts.app_label)
        self.model_name = force_text(self.opts.model_name)
        self.verbose_name = force_text(self.opts.verbose_name)
        self.verbose_name_plural = force_text(self.opts.verbose_name_plural)
        self.pk_attname = self.opts.pk.attname
        self.is_pagemodel = model_admin.is_pagemodel

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.deny_request_if_not_permitted()
        return super(WMABaseView, self).dispatch(request, *args, **kwargs)

    def deny_request_if_not_permitted(self):
        if not self.check_action_permitted(self.request.user):
            raise PermissionDenied

    def check_action_permitted(self, user):
        return True

    @cached_property
    def button_helper(self):
        return self.model_admin.get_button_helper_class()(self, self.request)

    @property
    def permission_helper(self):
        return self.model_admin.permission_helper

    @property
    def url_helper(self):
        return self.model_admin.url_helper

    @property
    def menu_icon(self):
        return self.model_admin.get_menu_icon()

    @property
    def header_icon(self):
        return self.menu_icon

    @property
    def index_url(self):
        return self.url_helper.index_url

    @property
    def create_url(self):
        return self.url_helper.create_url

    def get_page_title(self):
        return self.page_title or capfirst(self.opts.verbose_name_plural)

    def get_page_subtitle(self):
        return ''

    def get_meta_title(self):
        return self.meta_title or self.get_page_title()

    def get_base_queryset(self, request=None):
        return self.model_admin.get_queryset(request or self.request)

    def get_context_data(self, **kwargs):
        context = {
            'model_admin': self.model_admin,
        }
        context.update(kwargs)
        return super(WMABaseView, self).get_context_data(**context)


class ModelFormView(WMABaseView, FormView):

    def get_edit_handler_class(self):
        if hasattr(self.model, 'edit_handler'):
            edit_handler = self.model.edit_handler
        else:
            fields_to_exclude = self.model_admin.get_form_fields_exclude(request=self.request)
            panels = extract_panel_definitions_from_model_class(self.model, exclude=fields_to_exclude)
            edit_handler = ObjectList(panels)
        return edit_handler.bind_to_model(self.model)

    def get_form_class(self):
        return self.get_edit_handler_class().get_form_class(self.model)

    def get_success_url(self):
        return self.index_url

    def get_instance(self):
        """Return an instance for the ModelForm to use. An existing instance is
        used when the view has an `instance` attribute / cached property
        method. Otherwise, a fresh instance of self.model is returned"""
        return getattr(self, 'instance', None) or self.model()

    def get_form_kwargs(self):
        kwargs = FormView.get_form_kwargs(self)
        kwargs.update({'instance': self.get_instance()})
        return kwargs

    @property
    def media(self):
        return forms.Media(
            css={'all': self.model_admin.get_form_view_extra_css()},
            js=self.model_admin.get_form_view_extra_js()
        )

    def get_context_data(self, **kwargs):
        instance = self.get_instance()
        edit_handler_class = self.get_edit_handler_class()
        form = self.get_form()
        context = {
            'is_multipart': form.is_multipart(),
            'edit_handler': edit_handler_class(instance=instance, form=form),
            'form': form,
        }
        context.update(kwargs)
        return super(ModelFormView, self).get_context_data(**context)

    def get_success_message(self, instance):
        return _("{model_name} '{instance}' created.").format(
            model_name=capfirst(self.opts.verbose_name), instance=instance)

    def get_success_message_buttons(self, instance):
        button_url = self.url_helper.get_action_url('edit', quote(instance.pk))
        return [
            messages.button(button_url, _('Edit'))
        ]

    def get_error_message(self):
        model_name = self.verbose_name
        return _("The %s could not be created due to errors.") % model_name

    def form_valid(self, form):
        instance = form.save()
        messages.success(
            self.request, self.get_success_message(instance),
            buttons=self.get_success_message_buttons(instance)
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, self.get_error_message())
        return self.render_to_response(self.get_context_data())


class InstanceSpecificView(WMABaseView, SingleObjectMixin):
    instance_pk = None
    pk_url_kwarg = 'instance_pk'
    context_object_name = 'instance'

    def __init__(self, model_admin, **kwargs):
        super(InstanceSpecificView, self).__init__(model_admin, **kwargs)
        if 'instance_pk' in kwargs:
            warnings.warn(
                "'instance_pk' should no longer be passed to %s's as_view() "
                "method. It should be passed as a keyword argument to "
                "the 'view' method returned by as_view() instead" %
                self.__class__.__name__, category=RemovedInWagtail112Warning
            )

    @cached_property
    def instance(self):
        """
        Return the result of self.get_object() and cache it to avoid repeat
        database queries
        """
        return self.get_object()

    def get_object(self):
        """
        Returns an instance of self.model identified by URL parameters in the
        current request. Raises a 404 if no match is found.
        """
        # Ensure primary key value is unquoted and named as expected by
        # SingleObjectMixin.get_object()
        kwarg_key = self.pk_url_kwarg
        self.kwargs[kwarg_key] = unquote(
            self.kwargs.get(kwarg_key, self.instance_pk)
        )
        return super(InstanceSpecificView, self).get_object()

    def get_page_subtitle(self):
        return self.instance

    @property
    def pk_quoted(self):
        return quote(self.kwargs.get(self.pk_url_kwarg))

    @property
    def edit_url(self):
        return self.url_helper.get_action_url('edit', self.pk_quoted)

    @property
    def delete_url(self):
        return self.url_helper.get_action_url('delete', self.pk_quoted)

    def get_context_data(self, **kwargs):
        self.object = self.instance  # placate SingleObjectMixin
        return super(InstanceSpecificView, self).get_context_data(**kwargs)


class IndexView(WMABaseView):

    ORDER_VAR = 'o'
    ORDER_TYPE_VAR = 'ot'
    PAGE_VAR = 'p'
    SEARCH_VAR = 'q'
    ERROR_FLAG = 'e'
    IGNORED_PARAMS = (ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR)

    @property
    def media(self):
        return forms.Media(
            css={'all': self.model_admin.get_index_view_extra_css()},
            js=self.model_admin.get_index_view_extra_js()
        )

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_list(user)

    def get(self, request, *args, **kwargs):
        self.list_display = self.model_admin.get_list_display(request)
        self.list_filter = self.model_admin.get_list_filter(request)
        self.search_fields = self.model_admin.get_search_fields(request)
        self.items_per_page = self.model_admin.list_per_page
        self.select_related = self.model_admin.list_select_related

        # Get search parameters from the query string.
        try:
            self.page_num = int(request.GET.get(self.PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0

        self.params = dict(request.GET.items())
        if self.PAGE_VAR in self.params:
            del self.params[self.PAGE_VAR]
        if self.ERROR_FLAG in self.params:
            del self.params[self.ERROR_FLAG]

        self.query = request.GET.get(self.SEARCH_VAR, '')
        self.queryset = self.get_queryset(request)
        return super(IndexView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = self.request.user
        all_count = self.get_base_queryset().count()
        queryset = self.get_queryset()
        result_count = queryset.count()
        paginator = Paginator(queryset, self.items_per_page)

        try:
            page_obj = paginator.page(self.page_num + 1)
        except InvalidPage:
            page_obj = paginator.page(1)

        context = {
            'view': self,
            'all_count': all_count,
            'result_count': result_count,
            'paginator': paginator,
            'page_obj': page_obj,
            'object_list': page_obj.object_list,
            'user_can_create': self.permission_helper.user_can_create(user)
        }

        if self.is_pagemodel:
            models = self.model.allowed_parent_page_models()
            allowed_parent_types = [m._meta.verbose_name for m in models]
            valid_parents = self.permission_helper.get_valid_parent_pages(user)
            valid_parent_count = valid_parents.count()
            context.update({
                'no_valid_parents': not valid_parent_count,
                'required_parent_types': allowed_parent_types,
            })

        context.update(kwargs)
        return super(IndexView, self).get_context_data(**context)

    def get_buttons_for_obj(self, obj):
        return self.button_helper.get_buttons_for_obj(
            obj, classnames_add=['button-small', 'button-secondary'])

    def get_search_results(self, request, queryset, search_term):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        use_distinct = False
        if self.search_fields and search_term:
            orm_lookups = ['%s__icontains' % str(search_field)
                           for search_field in self.search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.opts, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct

    def lookup_allowed(self, lookup, value):
        # Check FKey lookups that are allowed, so that popups produced by
        # ForeignKeyRawIdWidget, on the basis of ForeignKey.limit_choices_to,
        # are allowed to work.
        for l in self.model._meta.related_fkey_lookups:
            for k, v in widgets.url_params_from_lookup_dict(l).items():
                if k == lookup and v == value:
                    return True

        parts = lookup.split(LOOKUP_SEP)

        # Last term in lookup is a query term (__exact, __startswith etc)
        # This term can be ignored.
        if len(parts) > 1 and parts[-1] in QUERY_TERMS:
            parts.pop()

        # Special case -- foo__id__exact and foo__id queries are implied
        # if foo has been specifically included in the lookup list; so
        # drop __id if it is the last part. However, first we need to find
        # the pk attribute name.
        rel_name = None
        for part in parts[:-1]:
            try:
                field = self.model._meta.get_field(part)
            except FieldDoesNotExist:
                # Lookups on non-existent fields are ok, since they're ignored
                # later.
                return True
            if hasattr(field, 'rel'):
                if field.rel is None:
                    # This property or relation doesn't exist, but it's allowed
                    # since it's ignored in ChangeList.get_filters().
                    return True
                model = field.rel.to
                rel_name = field.rel.get_related_field().name
            elif isinstance(field, ForeignObjectRel):
                model = field.model
                rel_name = model._meta.pk.name
            else:
                rel_name = None
        if rel_name and len(parts) > 1 and parts[-1] == rel_name:
            parts.pop()

        if len(parts) == 1:
            return True
        clean_lookup = LOOKUP_SEP.join(parts)
        return clean_lookup in self.list_filter

    def get_filters_params(self, params=None):
        """
        Returns all params except IGNORED_PARAMS
        """
        if not params:
            params = self.params
        lookup_params = params.copy()  # a dictionary of the query string
        # Remove all the parameters that are globally and systematically
        # ignored.
        for ignored in self.IGNORED_PARAMS:
            if ignored in lookup_params:
                del lookup_params[ignored]
        return lookup_params

    def get_filters(self, request):
        lookup_params = self.get_filters_params()
        use_distinct = False

        for key, value in lookup_params.items():
            if not self.lookup_allowed(key, value):
                raise DisallowedModelAdminLookup(
                    "Filtering by %s not allowed" % key)

        filter_specs = []
        if self.list_filter:
            for list_filter in self.list_filter:
                if callable(list_filter):
                    # This is simply a custom list filter class.
                    spec = list_filter(
                        request,
                        lookup_params,
                        self.model,
                        self.model_admin)
                else:
                    field_path = None
                    if isinstance(list_filter, (tuple, list)):
                        # This is a custom FieldListFilter class for a given
                        # field.
                        field, field_list_filter_class = list_filter
                    else:
                        # This is simply a field name, so use the default
                        # FieldListFilter class that has been registered for
                        # the type of the given field.
                        field = list_filter
                        field_list_filter_class = FieldListFilter.create
                    if not isinstance(field, models.Field):
                        field_path = field
                        field = get_fields_from_path(self.model,
                                                     field_path)[-1]
                    spec = field_list_filter_class(
                        field,
                        request,
                        lookup_params,
                        self.model,
                        self.model_admin,
                        field_path=field_path)

                    # Check if we need to use distinct()
                    use_distinct = (
                        use_distinct or lookup_needs_distinct(self.opts,
                                                              field_path))
                if spec and spec.has_output():
                    filter_specs.append(spec)

        # At this point, all the parameters used by the various ListFilters
        # have been removed from lookup_params, which now only contains other
        # parameters passed via the query string. We now loop through the
        # remaining parameters both to ensure that all the parameters are valid
        # fields and to determine if at least one of them needs distinct(). If
        # the lookup parameters aren't real fields, then bail out.
        try:
            for key, value in lookup_params.items():
                lookup_params[key] = prepare_lookup_value(key, value)
                use_distinct = (
                    use_distinct or lookup_needs_distinct(self.opts, key))
            return (
                filter_specs, bool(filter_specs), lookup_params, use_distinct
            )
        except FieldDoesNotExist as e:
            six.reraise(
                IncorrectLookupParameters,
                IncorrectLookupParameters(e),
                sys.exc_info()[2])

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in list(p):
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(sorted(p.items()))

    def _get_default_ordering(self):
        ordering = []
        if self.model_admin.ordering:
            ordering = self.model_admin.ordering
        elif self.opts.ordering:
            ordering = self.opts.ordering
        return ordering

    def get_default_ordering(self, request):
        if self.model_admin.get_ordering(request):
            return self.model_admin.get_ordering(request)
        if self.opts.ordering:
            return self.opts.ordering
        return ()

    def get_ordering_field(self, field_name):
        """
        Returns the proper model field name corresponding to the given
        field_name to use for ordering. field_name may either be the name of a
        proper model field or the name of a method (on the admin or model) or a
        callable with the 'admin_order_field' attribute. Returns None if no
        proper model field name can be matched.
        """
        try:
            field = self.opts.get_field(field_name)
            return field.name
        except FieldDoesNotExist:
            # See whether field_name is a name of a non-field
            # that allows sorting.
            if callable(field_name):
                attr = field_name
            elif hasattr(self.model_admin, field_name):
                attr = getattr(self.model_admin, field_name)
            else:
                attr = getattr(self.model, field_name)
            return getattr(attr, 'admin_order_field', None)

    def get_ordering(self, request, queryset):
        """
        Returns the list of ordering fields for the change list.
        First we check the get_ordering() method in model admin, then we check
        the object's default ordering. Then, any manually-specified ordering
        from the query string overrides anything. Finally, a deterministic
        order is guaranteed by ensuring the primary key is used as the last
        ordering field.
        """
        params = self.params
        ordering = list(self.get_default_ordering(request))
        if self.ORDER_VAR in params:
            # Clear ordering and used params
            ordering = []
            order_params = params[self.ORDER_VAR].split('.')
            for p in order_params:
                try:
                    none, pfx, idx = p.rpartition('-')
                    field_name = self.list_display[int(idx)]
                    order_field = self.get_ordering_field(field_name)
                    if not order_field:
                        continue  # No 'admin_order_field', skip it
                    # reverse order if order_field has already "-" as prefix
                    if order_field.startswith('-') and pfx == "-":
                        ordering.append(order_field[1:])
                    else:
                        ordering.append(pfx + order_field)
                except (IndexError, ValueError):
                    continue  # Invalid ordering specified, skip it.

        # Add the given query's ordering fields, if any.
        ordering.extend(queryset.query.order_by)

        # Ensure that the primary key is systematically present in the list of
        # ordering fields so we can guarantee a deterministic order across all
        # database backends.
        pk_name = self.opts.pk.name
        if not (set(ordering) & {'pk', '-pk', pk_name, '-' + pk_name}):
            # The two sets do not intersect, meaning the pk isn't present. So
            # we add it.
            ordering.append('-pk')

        return ordering

    def get_ordering_field_columns(self):
        """
        Returns an OrderedDict of ordering field column numbers and asc/desc
        """

        # We must cope with more than one column having the same underlying
        # sort field, so we base things on column numbers.
        ordering = self._get_default_ordering()
        ordering_fields = OrderedDict()
        if self.ORDER_VAR not in self.params:
            # for ordering specified on model_admin or model Meta, we don't
            # know the right column numbers absolutely, because there might be
            # morr than one column associated with that ordering, so we guess.
            for field in ordering:
                if field.startswith('-'):
                    field = field[1:]
                    order_type = 'desc'
                else:
                    order_type = 'asc'
                for index, attr in enumerate(self.list_display):
                    if self.get_ordering_field(attr) == field:
                        ordering_fields[index] = order_type
                        break
        else:
            for p in self.params[self.ORDER_VAR].split('.'):
                none, pfx, idx = p.rpartition('-')
                try:
                    idx = int(idx)
                except ValueError:
                    continue  # skip it
                ordering_fields[idx] = 'desc' if pfx == '-' else 'asc'
        return ordering_fields

    def get_queryset(self, request=None):
        request = request or self.request

        # First, we collect all the declared list filters.
        (self.filter_specs, self.has_filters, remaining_lookup_params,
         filters_use_distinct) = self.get_filters(request)

        # Then, we let every list filter modify the queryset to its liking.
        qs = self.get_base_queryset(request)
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(request, qs)
            if new_qs is not None:
                qs = new_qs

        try:
            # Finally, we apply the remaining lookup parameters from the query
            # string (i.e. those that haven't already been processed by the
            # filters).
            qs = qs.filter(**remaining_lookup_params)
        except (SuspiciousOperation, ImproperlyConfigured):
            # Allow certain types of errors to be re-raised as-is so that the
            # caller can treat them in a special way.
            raise
        except Exception as e:
            # Every other error is caught with a naked except, because we don't
            # have any other way of validating lookup parameters. They might be
            # invalid if the keyword arguments are incorrect, or if the values
            # are not in the correct type, so we might get FieldError,
            # ValueError, ValidationError, or ?.
            raise IncorrectLookupParameters(e)

        if not qs.query.select_related:
            qs = self.apply_select_related(qs)

        # Set ordering.
        ordering = self.get_ordering(request, qs)
        qs = qs.order_by(*ordering)

        # Apply search results
        qs, search_use_distinct = self.get_search_results(
            request, qs, self.query)

        # Remove duplicates from results, if necessary
        if filters_use_distinct | search_use_distinct:
            return qs.distinct()
        else:
            return qs

    def apply_select_related(self, qs):
        if self.select_related is True:
            return qs.select_related()

        if self.select_related is False:
            if self.has_related_field_in_list_display():
                return qs.select_related()

        if self.select_related:
            return qs.select_related(*self.select_related)
        return qs

    def has_related_field_in_list_display(self):
        for field_name in self.list_display:
            try:
                field = self.opts.get_field(field_name)
            except FieldDoesNotExist:
                pass
            else:
                if isinstance(field, models.ManyToOneRel):
                    return True
        return False

    def get_template_names(self):
        return self.model_admin.get_index_template()


class CreateView(ModelFormView):
    page_title = _('New')

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_create(user)

    def get(self, request, *args, **kwargs):
        if self.is_pagemodel:
            parents = self.permission_helper.get_valid_parent_pages(
                request.user)

            # There's only one available parent for this page type for this
            # user, so we send them along with that as the chosen parent page
            if parents.count() == 1:
                parent_pk = quote(parents.get().pk)
                return redirect(self.url_helper.get_action_url(
                    'add', self.app_label, self.model_name, parent_pk))

            # The page can be added in multiple places, so redirect to the
            # choose_parent view so that the parent can be specified
            return redirect(self.url_helper.get_action_url('choose_parent'))
        return super(CreateView, self).get(request, *args, **kwargs)

    def get_meta_title(self):
        return _('Create new %s') % self.verbose_name

    def get_page_subtitle(self):
        return capfirst(self.verbose_name)

    def get_template_names(self):
        return self.model_admin.get_create_template()


class EditView(InstanceSpecificView, ModelFormView):
    page_title = _('Editing')

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_edit_obj(user, self.instance)

    def get(self, request, *args, **kwargs):
        if self.is_pagemodel:
            return redirect(self.edit_url)
        return super(EditView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.is_pagemodel:
            return redirect(self.edit_url)
        return super(EditView, self).post(request, *args, **kwargs)

    def get_meta_title(self):
        return _('Editing %s') % self.verbose_name

    def get_success_message(self, instance):
        return _("{model_name} '{instance}' updated.").format(
            model_name=capfirst(self.verbose_name), instance=instance)

    def get_context_data(self, **kwargs):
        context = {
            'user_can_delete': self.permission_helper.user_can_delete_obj(
                self.request.user, self.instance)
        }
        context.update(kwargs)
        return super(EditView, self).get_context_data(**context)

    def get_error_message(self):
        name = self.verbose_name
        return _("The %s could not be saved due to errors.") % name

    def get_template_names(self):
        return self.model_admin.get_edit_template()


class ChooseParentView(FormView, WMABaseView):

    form_class = ParentChooserForm

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_create(user)

    def get_form_kwargs(self):
        kwargs = super(ChooseParentView, self).get_form_kwargs()
        kwargs.update({
            'valid_parents_qs': self.permission_helper.get_valid_parent_pages(
                self.request.user)
        })
        return kwargs

    def get_context_data(self, **kwargs):
        # Django 1.8 doesn't seem to work without this here
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()
        return super(ChooseParentView, self).get_context_data(**kwargs)

    def get_page_title(self):
        return _('Add %s') % self.verbose_name

    def form_valid(self, form):
        parent_pk = quote(form.cleaned_data['parent_page'].pk)
        return redirect(self.url_helper.get_action_url(
            'add', self.app_label, self.model_name, parent_pk))

    def get_template_names(self):
        return self.model_admin.get_choose_parent_template()


class DeleteView(InstanceSpecificView):
    page_title = _('Delete')

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_delete_obj(user, self.instance)

    def get(self, request, *args, **kwargs):
        if self.is_pagemodel:
            return redirect(self.delete_url)
        return super(DeleteView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.is_pagemodel:
            return redirect(self.delete_url)
        try:
            msg = _("{model} '{instance}' deleted.").format(
                model=self.verbose_name, instance=self.instance)
            self.delete_instance()
            messages.success(request, msg)
            return redirect(self.index_url)
        except models.ProtectedError:
            linked_objects = []
            fields = self.model._meta.fields_map.values()
            fields = (obj for obj in fields if not isinstance(
                obj.field, ManyToManyField))
            for rel in fields:
                if rel.on_delete == models.PROTECT:
                    qs = getattr(self.instance, rel.get_accessor_name())
                    for obj in qs.all():
                        linked_objects.append(obj)
            context = self.get_context_data(
                protected_error=True,
                linked_objects=linked_objects
            )
            return self.render_to_response(context)

    def get_meta_title(self):
        return _('Confirm deletion of %s') % self.verbose_name

    def confirmation_message(self):
        return _(
            "Are you sure you want to delete this %s? If other things in your "
            "site are related to it, they may also be affected."
        ) % self.verbose_name

    def delete_instance(self):
        self.instance.delete()

    def get_template_names(self):
        return self.model_admin.get_delete_template()


class InspectView(InstanceSpecificView):

    page_title = _('Inspecting')

    def check_action_permitted(self, user):
        return self.permission_helper.user_can_inspect_obj(user, self.instance)

    @property
    def media(self):
        return forms.Media(
            css={'all': self.model_admin.get_inspect_view_extra_css()},
            js=self.model_admin.get_inspect_view_extra_js()
        )

    def get_meta_title(self):
        return _('Inspecting %s') % self.verbose_name

    def get_field_label(self, field_name, field=None):
        """ Return a label to display for a field """
        label = None
        if field is not None:
            label = getattr(field, 'verbose_name', None)
            if label is None:
                label = getattr(field, 'name', None)
        if label is None:
            label = field_name
        return label

    def get_field_display_value(self, field_name, field=None):
        """ Return a display value for a field/attribute """

        # First we check for a 'get_fieldname_display' property/method on
        # the model, and return the value of that, if present.
        val_funct = getattr(self.instance, 'get_%s_display' % field_name, None)
        if val_funct is not None:
            if callable(val_funct):
                return val_funct()
            return val_funct

        # Now let's get the attribute value from the instance itself and see if
        # we can render something useful. raises AttributeError appropriately.
        val = getattr(self.instance, field_name)

        if isinstance(val, models.Manager):
            val = val.all()

        if isinstance(val, models.QuerySet):
            if val.exists():
                return ', '.join(['%s' % obj for obj in val])
            return self.model_admin.get_empty_value_display(field_name)

        # wagtail.wagtailimages might not be installed
        try:
            from wagtail.wagtailimages.models import AbstractImage
            if isinstance(val, AbstractImage):
                # Render a rendition of the image
                return self.get_image_field_display(field_name, field)
        except RuntimeError:
            pass

        # wagtail.wagtaildocuments might not be installed
        try:
            from wagtail.wagtaildocs.models import AbstractDocument
            if isinstance(val, AbstractDocument):
                # Render a link to the document
                return self.get_document_field_display(field_name, field)
        except RuntimeError:
            pass

        # Resort to returning the real value or 'empty value'
        if val or val is False:
            return val
        return self.model_admin.get_empty_value_display(field_name)

    def get_image_field_display(self, field_name, field):
        """ Render an image """
        from wagtail.wagtailimages.shortcuts import get_rendition_or_not_found
        image = getattr(self.instance, field_name)
        if image:
            return get_rendition_or_not_found(image, 'max-400x400').img_tag
        return self.model_admin.get_empty_value_display(field_name)

    def get_document_field_display(self, field_name, field):
        """ Render a link to a document """
        document = getattr(self.instance, field_name)
        if document:
            return mark_safe(
                '<a href="%s">%s <span class="meta">(%s, %s)</span></a>' % (
                    document.url,
                    document.title,
                    document.file_extension.upper(),
                    filesizeformat(document.file.size),
                )
            )
        return self.model_admin.get_empty_value_display(field_name)

    def get_dict_for_field(self, field_name):
        """
        Return a dictionary containing `label` and `value` values to display
        for a field.
        """
        try:
            field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            field = None
        return {
            'label': self.get_field_label(field_name, field),
            'value': self.get_field_display_value(field_name, field),
        }

    def get_fields_dict(self):
        """
        Return a list of `label`/`value` dictionaries to represent the
        fiels named by the model_admin class's `get_inspect_view_fields` method
        """
        fields = []
        for field_name in self.model_admin.get_inspect_view_fields():
            fields.append(self.get_dict_for_field(field_name))
        return fields

    def get_context_data(self, **kwargs):
        context = {
            'fields': self.get_fields_dict(),
            'buttons': self.button_helper.get_buttons_for_obj(
                self.instance, exclude=['inspect']),
        }
        context.update(kwargs)
        return super(InspectView, self).get_context_data(**context)

    def get_template_names(self):
        return self.model_admin.get_inspect_template()
