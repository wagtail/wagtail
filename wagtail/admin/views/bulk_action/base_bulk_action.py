from abc import ABC, abstractmethod

from django import forms
from django.db import transaction
from django.shortcuts import get_list_or_404, redirect
from django.views.generic import FormView

from wagtail.admin import messages
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.core import hooks


class BulkAction(ABC, FormView):
    @property
    @abstractmethod
    def display_name(self):
        pass

    @property
    @abstractmethod
    def action_type(self):
        pass

    @property
    @abstractmethod
    def aria_label(self):
        pass

    extras = dict()
    action_priority = 100
    models = []
    classes = set()

    form_class = forms.Form
    cleaned_form = None

    def __init__(self, request, model):
        self.request = request
        next_url = get_valid_next_url_from_request(request)
        if not next_url:
            next_url = request.path
        self.next_url = next_url
        self.num_parent_objects = self.num_child_objects = 0
        if model in self.models:
            self.model = model
        else:
            raise Exception("model {} is not among the specified list of models".format(model.__class__.__name__))

    @classmethod
    def get_queryset(cls, model, object_ids):
        return get_list_or_404(model, pk__in=object_ids)

    def check_perm(self, obj):
        return True

    @classmethod
    def execute_action(cls, objects, **kwargs):
        raise NotImplementedError("execute_action needs to be implemented")

    def get_success_message(self, num_parent_objects, num_child_objects):
        pass

    def object_context(self, obj):
        return {
            'item': obj
        }

    @classmethod
    def get_default_model(cls):
        if len(cls.models) == 1:
            return cls.models[0]
        raise Exception("Cannot get default model if number of models is greater than 1")

    def __run_before_hooks(self, action_type, request, objects):
        for hook in hooks.get_hooks('before_bulk_action'):
            result = hook(request, action_type, objects, self)
            if hasattr(result, 'status_code'):
                return result

    def __run_after_hooks(self, action_type, request, objects):
        for hook in hooks.get_hooks('after_bulk_action'):
            result = hook(request, action_type, objects, self)
            if hasattr(result, 'status_code'):
                return result

    def get_all_objects_in_listing_query(self, parent_id):
        return self.model.objects.all().values_list('pk', flat=True)

    def get_actionable_objects(self):
        objects = []
        items_with_no_access = []
        object_ids = self.request.GET.getlist('id')
        if 'all' in object_ids:
            object_ids = self.get_all_objects_in_listing_query(self.request.GET.get('childOf'))

        for obj in self.get_queryset(self.model, object_ids):
            if not self.check_perm(obj):
                items_with_no_access.append(obj)
            else:
                objects.append(obj)
        return objects, {
            'items_with_no_access': items_with_no_access
        }

    def get_context_data(self, **kwargs):
        items, items_with_no_access = self.get_actionable_objects()
        _items = []
        for item in items:
            _items.append(self.object_context(item))
        return {
            **super().get_context_data(**kwargs),
            'items': _items,
            **items_with_no_access,
            'next': self.next_url,
            'submit_url': self.request.path + '?' + self.request.META['QUERY_STRING'],
        }

    def prepare_action(self, objects, objects_without_access):
        return

    def get_execution_context(self):
        return {}

    def form_valid(self, form):
        request = self.request
        self.cleaned_form = form
        objects, objects_without_access = self.get_actionable_objects()
        resp = self.prepare_action(objects, objects_without_access)
        if hasattr(resp, 'status_code'):
            return resp
        with transaction.atomic():
            before_hook_result = self.__run_before_hooks(self.action_type, request, objects)
            if before_hook_result is not None:
                return before_hook_result
            num_parent_objects, num_child_objects = self.execute_action(objects, **self.get_execution_context())
            after_hook_result = self.__run_after_hooks(self.action_type, request, objects)
            if after_hook_result is not None:
                return after_hook_result
            success_message = self.get_success_message(num_parent_objects, num_child_objects)
            if success_message is not None:
                messages.success(request, success_message)
        return redirect(self.next_url)

    def form_invalid(self, form):
        return super().form_invalid(form)
