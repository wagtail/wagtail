import json

from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import AdminChooser
from wagtail.core.models import Task


class AdminTaskChooser(AdminChooser):
    choose_one_text = _('Choose a task')
    choose_another_text = _('Choose another task')
    link_to_chosen_text = _('Edit this task')

    def render_html(self, name, value, attrs):
        task, value = self.get_instance_and_id(Task, value)
        original_field_html = super().render_html(name, value, attrs)

        return render_to_string("wagtailadmin/workflows/widgets/task_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'display_title': task.name if task else '',
            'edit_url': reverse('wagtailadmin_workflows:edit_task', args=[task.id]) if task else '',
        })

    def render_js_init(self, id_, name, value):
        return "createTaskChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailadmin/js/task-chooser-modal.js'),
            versioned_static('wagtailadmin/js/task-chooser.js'),
        ])
