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

    num_child_objects = 0
    num_parent_objects = 0
    extras = dict()
    action_priority = 100
    model = None
    object_key = 'object'
    classes = set()

    form_class = forms.Form
    cleaned_form = None

    def __init__(self, request):
        self.request = request
        next_url = get_valid_next_url_from_request(request)
        if not next_url:
            next_url = request.path
        self.next_url = next_url

    @classmethod
    def get_queryset(cls, object_ids):
        if cls.model is None:
            raise Exception("model should be provided")
        return get_list_or_404(cls.model, id__in=object_ids)

    def check_perm(self, obj):
        return True

    @classmethod
    def execute_action(cls, objects, **kwargs):
        raise NotImplementedError("execute_action needs to be implemented")

    def get_success_message(self):
        pass

    def object_context(self, obj):
        return {
            '{}'.format(self.object_key): obj
        }

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

    def get_actionable_objects(self):
        objects = []
        objects_with_no_access = []
        object_ids = self.request.GET.getlist('id')
        if 'all' in object_ids:
            parent_page_id = int(self.request.GET.get('childOf'))
            object_ids = self.model.objects.get(id=parent_page_id).get_children().values_list('id', flat=True)
        object_ids = list(map(int, object_ids))

        for obj in self.get_queryset(object_ids):
            if not self.check_perm(obj):
                objects_with_no_access.append(obj)
            else:
                objects.append(obj)
        return objects, objects_with_no_access

    def get_context_data(self, **kwargs):
        objects, objects_with_no_access = self.get_actionable_objects()
        _objects = []
        for obj in objects:
            _objects.append(self.object_context(obj))
        return {
            **super().get_context_data(**kwargs),
            '{}s'.format(self.object_key): _objects,
            '{}s_with_no_access'.format(self.object_key): objects_with_no_access,
            'next': self.next_url,
            'submit_url': self.request.path + '?' + self.request.META['QUERY_STRING'],
        }

    def prepare_action(self, objects):
        return

    def get_execution_context(self):
        return {}

    def form_valid(self, form):
        request = self.request
        self.cleaned_form = form
        objects, _ = self.get_actionable_objects()
        resp = self.prepare_action(objects)
        if hasattr(resp, 'status_code'):
            return resp
        with transaction.atomic():
            before_hook_result = self.__run_before_hooks(self.action_type, request, objects)
            if before_hook_result is not None:
                return before_hook_result
            self.execute_action(objects, **self.get_execution_context())
            after_hook_result = self.__run_after_hooks(self.action_type, request, objects)
            if after_hook_result is not None:
                return after_hook_result
            success_message = self.get_success_message()
            if success_message is not None:
                messages.success(request, success_message)
        return redirect(self.next_url)

    def form_invalid(self, form):
        return super().form_invalid(form)
