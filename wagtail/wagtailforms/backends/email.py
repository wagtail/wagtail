import datetime

from django.core.exceptions import ImproperlyConfigured
from .base import BaseFormProcessor
from wagtail.wagtailadmin import tasks


class EmailFormProcessor(BaseFormProcessor):
    def __init__(self):
        pass

    @staticmethod
    def validate_usage(page):
        try:
            page._meta.get_field('subject')
            page._meta.get_field('to_address')
            page._meta.get_field('from_address')
        except:
            raise ImproperlyConfigured("To use the EmailFormProcessor your Page must define the fields: subject, to_address and from_address.")

    def process(self, page, form):
        content = ', '.join([x[1].label + ': ' + form.data.get(x[0]) for x in form.fields.items()])
        tasks.send_email_task.delay(page.subject, content, [page.to_address], page.from_address,)
