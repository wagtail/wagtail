import datetime 

from django.core.exceptions import ImproperlyConfigured
from .base import BaseFormProcessor
from wagtail.wagtailadmin import tasks


class EmailFormProcessor(BaseFormProcessor):
    def __init__(self):
        pass
    
    def validate_usage(page):
        return True
        
    def process(self, page, form):
        content = ', '.join([ x[1].label +': '+ form.data.get(x[0]) for x in form.fields.items() ])
        tasks.send_email_task.delay("New " + page.title+" form submission at " + str(datetime.datetime.now()) , content, page.email_from, [page.email_to] )
