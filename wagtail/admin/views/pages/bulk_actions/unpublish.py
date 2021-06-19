from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.core import hooks


class UnpublishBulkAction(PageBulkAction):
    display_name = _("Unpublish")
    action_type = "unpublish"
    aria_label = _("Unpublish pages")
    template_name = "wagtailadmin/pages/bulk_actions/confirm_bulk_unpublish.html"

    def check_perm(self, page):
        return page.permissions_for_user(self.request.user).can_unpublish()

    def object_context(self, page):
        return {
            **super().object_context(page),
            'live_descendant_count': page.get_descendants().live().count(),
        }
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_live_descendants'] = any(map(lambda x: x['live_descendant_count'] > 0, context['pages']))
        return context

    def execute_action(cls, pages):
        for page in pages:
            page.unpublish(user=cls.request.user)
            cls.num_parent_objects += 1

            if cls.include_descendants:
                for live_descendant_page in page.get_descendants().live().defer_streamfields().specific():
                    if cls.check_perm(live_descendant_page):
                        live_descendant_page.unpublish()
                        cls.num_child_objects += 1

    def get_success_message(self):
        if self.num_parent_objects == 1:
            if self.include_descendants:
                if self.num_child_objects == 0:
                    success_message = _("1 page has been unpublished")
                else:
                    success_message = ngettext(
                        "1 page and %(num_child_objects)d child page have been unpublished",
                        "1 page and %(num_child_objects)d child pages have been unpublished",
                        self.num_child_objects
                    ) % {
                        'num_child_objects': self.num_child_objects
                    }
            else:
                success_message = _("1 page has been unpublished")
        else:
            if self.include_descendants:
                if self.num_child_objects == 0:
                    success_message = _("%(num_parent_objects)d pages have been unpublished") % {'num_parent_objects': self.num_parent_objects}
                else:
                    success_message = ngettext(
                        "%(num_parent_objects)d pages and %(num_child_objects)d child page have been unpublished",
                        "%(num_parent_objects)d pages and %(num_child_objects)d child pages have been unpublished",
                        self.num_child_objects
                    ) % {
                        'num_child_objects': self.num_child_objects,
                        'num_parent_objects': self.num_parent_objects
                    }
            else:
                success_message = _("%(num_parent_objects)d pages have been unpublished") % {'num_parent_objects': self.num_parent_objects}
        return success_message

@hooks.register('register_page_bulk_action')
def unpublish(request, parent_page_id):
    return UnpublishBulkAction(request, parent_page_id)
