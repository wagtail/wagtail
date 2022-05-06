import json

from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import BaseChooser
from wagtail.models import Task


class AdminTaskChooser(BaseChooser):
    choose_one_text = _("Choose a task")
    choose_another_text = _("Choose another task")
    link_to_chosen_text = _("Edit this task")
    model = Task
    template_name = "wagtailadmin/workflows/widgets/task_chooser.html"

    def get_value_data(self, value):
        if value is None:
            return None
        elif isinstance(value, self.model):
            instance = value
        else:  # assume ID
            instance = self.model.objects.get(pk=value)

        edit_url = AdminURLFinder().get_edit_url(instance)

        return {
            "id": instance.pk,
            "title": instance.name,
            "edit_url": edit_url,
        }

    def get_context(self, name, value_data, attrs):
        value_data = value_data or {}
        original_field_html = self.render_hidden_input(
            name, value_data.get("id"), attrs
        )
        return {
            "widget": self,
            "original_field_html": original_field_html,
            "attrs": attrs,
            "value": bool(
                value_data
            ),  # only used by chooser.html to identify blank values,
            "display_title": value_data.get("title", ""),
            "edit_url": value_data.get("edit_url", ""),
            "classname": "task-chooser",
            "chooser_url": reverse("wagtailadmin_workflows:task_chooser"),
        }

    def render_html(self, name, value_data, attrs):
        return render_to_string(
            self.template_name,
            self.get_context(name, value_data, attrs),
        )

    def render_js_init(self, id_, name, value_data):
        return "createTaskChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/task-chooser-modal.js"),
                versioned_static("wagtailadmin/js/task-chooser.js"),
            ]
        )
