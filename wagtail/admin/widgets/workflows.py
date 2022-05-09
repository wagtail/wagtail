import json

from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import BaseChooser
from wagtail.models import Task


class AdminTaskChooser(BaseChooser):
    choose_one_text = _("Choose a task")
    choose_another_text = _("Choose another task")
    link_to_chosen_text = _("Edit this task")
    model = Task
    template_name = "wagtailadmin/workflows/widgets/task_chooser.html"

    def get_value_data_from_instance(self, instance):
        data = super().get_value_data_from_instance(instance)
        data["title"] = instance.name
        return data

    def get_context(self, name, value_data, attrs):
        context = super().get_context(name, value_data, attrs)
        context.update(
            {
                "display_title": value_data.get("title", ""),
                "classname": "task-chooser",
                "chooser_url": reverse("wagtailadmin_workflows:task_chooser"),
            }
        )
        return context

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
