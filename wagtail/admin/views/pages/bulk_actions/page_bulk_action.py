from wagtail.admin.views.bulk_action import BulkAction
from wagtail.core.models import Page

class PageBulkAction(BulkAction):
    model = Page
    object_key = 'page'
