from .base import BaseFormProcessor
from wagtail.wagtailadmin import tasks


class EmailFormProcessor(BaseFormProcessor):
    def __init__(self):
        pass

    def process(self, page, form):
        if page.to_address:
            content = '\n'.join([x[1].label + ': ' + form.data.get(x[0]) for x in form.fields.items()])
            tasks.send_email_task.delay(page.subject, content, [page.to_address], page.from_address,)
