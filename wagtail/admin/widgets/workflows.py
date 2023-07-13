import json

from django import forms
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import BaseChooser
from wagtail.models import Task


class AdminTaskChooser(BaseChooser):
    choose_one_text = _("Choose a task")
    choose_another_text = _("Choose another task")
    link_to_chosen_text = _("Edit this task")
    model = Task
    icon = "thumbtack"
    chooser_modal_url_name = "wagtailadmin_workflows:task_chooser"
    classname = "task-chooser"

    def render_js_init(self, id_, name, value_data):
        return f"createTaskChooser({json.dumps(id_)});"

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/task-chooser-modal.js"),
                versioned_static("wagtailadmin/js/task-chooser.js"),
            ]
        )
