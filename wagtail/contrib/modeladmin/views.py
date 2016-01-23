import sys
import operator
from collections import OrderedDict
from functools import reduce

from django.db import models
from django.db.models.fields.related import ForeignObjectRel
from django.db.models.constants import LOOKUP_SEP
from django.db.models.sql.constants import QUERY_TERMS
from django.shortcuts import get_object_or_404, redirect, render
from django.core.urlresolvers import reverse

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.db.models.fields import FieldDoesNotExist

from django.core.paginator import Paginator, InvalidPage

from django.contrib.admin import FieldListFilter, widgets
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.exceptions import DisallowedModelAdminLookup
from django.contrib.admin.utils import (
    get_fields_from_path, lookup_needs_distinct, prepare_lookup_value, quote)

from django.utils import six
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.utils.http import urlencode
from django.utils.functional import cached_property
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.edit_handlers import (
    ObjectList, extract_panel_definitions_from_model_class)

from .helpers import get_url_name, ButtonHelper, PageButtonHelper
from .forms import ParentChooserForm

# IndexView settings
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
ERROR_FLAG = 'e'
IGNORED_PARAMS = (ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR)

# Page URL name settings
# > v1.1
PAGES_CREATE_URL_NAME = 'wagtailadmin_pages:add'
PAGES_EDIT_URL_NAME = 'wagtailadmin_pages:edit'
PAGES_UNPUBLISH_URL_NAME = 'wagtailadmin_pages:unpublish'
PAGES_DELETE_URL_NAME = 'wagtailadmin_pages:delete'
PAGES_COPY_URL_NAME = 'wagtailadmin_pages:copy'


class WMABaseView(TemplateView):
    """
    Groups together common functionality for all app views.
    """
    modeladmin = None
    meta_title = ''
    page_title = ''
    page_subtitle = ''

    def __init__(self, modeladmin):
        self.modeladmin = modeladmin
        self.model = modeladmin.model
        self.opts = modeladmin.model._meta
        self.pk_attname = self.opts.pk.attname
        self.is_pagemodel = modeladmin.is_pagemodel
        self.permission_helper = modeladmin.permission_helper

    @cached_property
    def app_label(self):
        return capfirst(force_text(self.opts.app_label))

    @cached_property
    def model_name(self):
        return capfirst(force_text(self.opts.verbose_name))

    @cached_property
    def model_name_plural(self):
        return capfirst(force_text(self.opts.verbose_name_plural))

    @cached_property
    def get_index_url(self):
        return self.modeladmin.get_index_url()

    @cached_property
    def get_create_url(self):
        return self.modeladmin.get_create_url()

    @cached_property
    def menu_icon(self):
        return self.modeladmin.get_menu_icon()

    @cached_property
    def header_icon(self):
        return self.menu_icon

    def permission_denied_response(self):
        """Return a standard 'permission denied' response"""
        messages.error(
            self.request,
            _('Sorry, you do not have permission to access that area.')
        )
        return redirect('wagtailadmin_home')

    def get_edit_url(self, obj):
        return reverse(get_url_name(self.opts, 'edit'), args=(obj.pk,))

    def get_delete_url(self, obj):
        return reverse(get_url_name(self.opts, 'delete'), args=(obj.pk,))

    def prime_session_for_redirection(self):
        self.request.session['return_to_index_url'] = self.get_index_url

    def get_page_title(self):
        return self.page_title or self.model_name_plural

    def get_meta_title(self):
        return self.meta_title or self.get_page_title()

    def get_base_queryset(self, request):
        return self.modeladmin.get_queryset(request)


class WMAFormView(WMABaseView, FormView):

    def get_edit_handler_class(self):
        panels = extract_panel_definitions_from_model_class(self.model)
        return ObjectList(panels).bind_to_model(self.model)

    def get_form_class(self):
        return self.get_edit_handler_class().get_form_class(self.model)

    def get_success_url(self):
        return self.get_index_url

    def get_instance(self):
        return getattr(self, 'instance', None) or self.model()

    def get_form_kwargs(self):
        kwargs = FormView.get_form_kwargs(self)
        kwargs.update({'instance': self.get_instance()})
        return kwargs

    def get_context_data(self, **kwargs):
        instance = self.get_instance()
        edit_handler_class = self.get_edit_handler_class()
        form = self.get_form()
        return {
            'view': self,
            'is_multipart': form.is_multipart(),
            'edit_handler': edit_handler_class(instance=instance, form=form)
        }

    def get_success_message(self, instance):
        return _("{model_name} '{instance}' created.").format(
            model_name=self.model_name, instance=instance)

    def get_success_message_buttons(self, instance):
        return [
            messages.button(self.get_edit_url(instance), _('Edit'))
        ]

    def get_error_message(self):
        model_name = self.model_name.lower()
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


class ObjectSpecificView(WMABaseView):

    object_id = None
    instance = None

    def __init__(self, modeladmin, object_id):
        super(ObjectSpecificView, self).__init__(modeladmin)
        self.object_id = object_id
        self.pk_safe = quote(object_id)
        filter_kwargs = {}
        filter_kwargs[self.pk_attname] = self.pk_safe
        object_qs = modeladmin.model._default_manager.get_queryset().filter(
            **filter_kwargs)
        self.instance = get_object_or_404(object_qs)

    def check_action_permitted(self):
        return True

    def get_edit_url(self, obj=None):
        return reverse(get_url_name(self.opts, 'edit'), args=(self.pk_safe,))

    def get_delete_url(self, obj=None):
        return reverse(get_url_name(self.opts, 'confirm_delete'),
                       args=(self.pk_safe,))


class IndexView(WMABaseView):

    button_helper_class = None

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.list_display = self.modeladmin.get_list_display(request)
        self.list_filter = self.modeladmin.get_list_filter(request)
        self.search_fields = self.modeladmin.get_search_fields(request)
        self.items_per_page = self.modeladmin.list_per_page
        self.select_related = self.modeladmin.list_select_related
        request = self.request

        # Get search parameters from the query string.
        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0

        self.params = dict(request.GET.items())
        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]
        if ERROR_FLAG in self.params:
            del self.params[ERROR_FLAG]

        self.query = request.GET.get(SEARCH_VAR, '')
        self.queryset = self.get_queryset(request)

        if not self.permission_helper.allow_list_view(request.user):
            return self.permission_denied_response()
        return super(IndexView, self).dispatch(request, *args, **kwargs)

    def get_button_helper_class(self, user, obj):
        if self.button_helper_class:
            return self.button_helper_class
        if self.is_pagemodel:
            return PageButtonHelper
        return ButtonHelper


    def get_action_buttons_for_obj(self, user, obj):
        helper_class = self.get_button_helper_class(user, obj)
        helper = helper_class(self.model, self.permission_helper, user, obj)
        return helper.get_permitted_buttons()


    def get_search_results(self, request, queryset, search_term):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        if self.search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
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
                field, _, _, _ = self.model._meta.get_field_by_name(part)
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
        for ignored in IGNORED_PARAMS:
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
                        self.modeladmin)
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
                        self.modeladmin,
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
        if self.modeladmin.ordering:
            ordering = self.modeladmin.ordering
        elif self.opts.ordering:
            ordering = self.opts.ordering
        return ordering

    def get_default_ordering(self, request):
        if self.modeladmin.get_ordering(request):
            return self.modeladmin.get_ordering(request)
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
            elif hasattr(self.modeladmin, field_name):
                attr = getattr(self.modeladmin, field_name)
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
        if ORDER_VAR in params:
            # Clear ordering and used params
            ordering = []
            order_params = params[ORDER_VAR].split('.')
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
        if ORDER_VAR not in self.params:
            # for ordering specified on modeladmin or model Meta, we don't
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
            for p in self.params[ORDER_VAR].split('.'):
                none, pfx, idx = p.rpartition('-')
                try:
                    idx = int(idx)
                except ValueError:
                    continue  # skip it
                ordering_fields[idx] = 'desc' if pfx == '-' else 'asc'
        return ordering_fields

    def get_queryset(self, request):
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

    def get_context_data(self, request, *args, **kwargs):
        user = request.user
        has_add_permission = self.permission_helper.has_add_permission(user)
        all_count = self.get_base_queryset(request).count()
        queryset = self.get_queryset(request)
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
            'has_add_permission': has_add_permission,
        }

        if self.is_pagemodel:
            allowed_parent_types = self.model.allowed_parent_page_types()
            user = request.user
            valid_parents = self.permission_helper.get_valid_parent_pages(user)
            valid_parent_count = valid_parents.count()
            context.update({
                'no_valid_parents': not valid_parent_count,
                'required_parent_types': allowed_parent_types,
            })
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, *args, **kwargs)
        if request.session.get('return_to_index_url'):
            del(request.session['return_to_index_url'])
        return self.render_to_response(context)

    def get_template_names(self):
        return self.modeladmin.get_index_template()


class CreateView(WMAFormView):
    page_title = _('New')

    def dispatch(self, request, *args, **kwargs):
        if not self.permission_helper.has_add_permission(request.user):
            return self.permission_denied_response()

        if self.is_pagemodel:
            self.prime_session_for_redirection()
            user = request.user
            parents = self.permission_helper.get_valid_parent_pages(user)
            parent_count = parents.count()

            # There's only one available parent for this page type for this
            # user, so we send them along with that as the chosen parent page
            if parent_count == 1:
                parent = parents.get()
                return redirect(
                    PAGES_CREATE_URL_NAME, self.opts.app_label,
                    self.opts.model_name, parent.pk)

            # The page can be added in multiple places, so redirect to the
            # choose_parent view so that the parent can be specified
            return redirect(self.modeladmin.get_choose_parent_url())
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_meta_title(self):
        return _('Create new %s') % self.model_name.lower()

    def get_page_subtitle(self):
        return self.model_name

    def get_template_names(self):
        return self.modeladmin.get_create_template()


class ChooseParentView(WMABaseView):
    def dispatch(self, request, *args, **kwargs):
        if not self.permission_helper.has_add_permission(request.user):
            return self.permission_denied_response()
        return super(ChooseParentView, self).dispatch(request, *args, **kwargs)

    def get_page_title(self):
        return _('Add %s') % self.model_name

    def get_form(self, request):
        parents = self.permission_helper.get_valid_parent_pages(request.user)
        return ParentChooserForm(parents, request.POST or None)

    def get(self, request, *args, **kwargs):
        form = self.get_form(request)
        context = {'view': self, 'form': form}
        return render(request, self.get_template(), context)

    def post(self, request, *args, **kargs):
        form = self.get_form(request)
        if form.is_valid():
            parent = form.cleaned_data['parent_page']
            return redirect(PAGES_CREATE_URL_NAME, self.opts.app_label,
                            self.opts.model_name, quote(parent.pk))
        context = {'view': self, 'form': form}
        return render(request, self.get_template(), context)

    def get_template(self):
        return self.modeladmin.get_choose_parent_template()


class EditView(ObjectSpecificView, CreateView):
    page_title = _('Editing')

    def check_action_permitted(self):
        user = self.request.user
        return self.permission_helper.can_edit_object(user, self.instance)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted():
            return self.permission_denied_response()
        if self.is_pagemodel:
            self.prime_session_for_redirection()
            return redirect(PAGES_EDIT_URL_NAME, self.object_id)
        return super(CreateView, self).dispatch(request, *args, **kwargs)

    def get_meta_title(self):
        return _('Editing %s') % self.model_name.lower()

    def page_subtitle(self):
        return self.instance

    def get_success_message(self, instance):
        return _("{model_name} '{instance}' updated.").format(
            model_name=self.model_name, instance=instance)

    def get_error_message(self):
        model_name = self.model_name.lower()
        return _("The %s could not be saved due to errors.") % model_name

    def get_template_names(self):
        return self.modeladmin.get_edit_template()


class ConfirmDeleteView(ObjectSpecificView):
    page_title = _('Delete')

    def check_action_permitted(self):
        user = self.request.user
        return self.permission_helper.can_delete_object(user, self.instance)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted():
            return self.permission_denied_response()
        if self.is_pagemodel:
            self.prime_session_for_redirection()
            return redirect(PAGES_DELETE_URL_NAME, self.object_id)
        return super(ConfirmDeleteView, self).dispatch(request, *args,
                                                       **kwargs)

    def get_meta_title(self):
        return _('Confirm deletion of %s') % self.model_name.lower()

    def get_page_subtitle(self):
        return self.instance

    def confirmation_message(self):
        return _(
            "Are you sure you want to delete this %s? If other things in your "
            "site are related to it, they may also be affected."
        ) % self.model_name

    def get(self, request, *args, **kwargs):
        instance = self.instance
        if request.POST:
            instance.delete()
            messages.success(
                request,
                _("{model_name} '{instance}' deleted.").format(
                    model_name=self.model_name, instance=instance))
            return redirect(self.get_index_url)

        context = {'view': self, 'instance': self.instance}
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_template_names(self):
        return self.modeladmin.get_confirm_delete_template()


class UnpublishRedirectView(ObjectSpecificView):
    def check_action_permitted(self):
        user = self.request.user
        return self.permission_helper.can_unpublish_object(user, self.instance)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted():
            return self.permission_denied_response()
        self.prime_session_for_redirection()
        return redirect(PAGES_UNPUBLISH_URL_NAME, self.object_id)


class CopyRedirectView(ObjectSpecificView):
    def check_action_permitted(self):
        user = self.request.user
        return self.permission_helper.can_copy_object(user, self.instance)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.check_action_permitted():
            return self.permission_denied_response()
        self.prime_session_for_redirection()
        return redirect(PAGES_COPY_URL_NAME, self.object_id)
