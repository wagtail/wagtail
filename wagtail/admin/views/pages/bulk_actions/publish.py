from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction
from wagtail.core import hooks


class PublishBulkAction(PageBulkAction):
    display_name = _("Publish")
    action_type = "publish"
    aria_label = _("Publish pages")
    template_name = "wagtailadmin/pages/bulk_actions/confirm_bulk_publish.html"

    def check_perm(self, page):
        return page.permissions_for_user(self.request.user).can_publish()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_draft_descendants'] = any(map(lambda x: x['page'].get_descendants().not_live().count(), context['pages']))
        return context

    def execute_action(cls, pages):
        for page in pages:
            revision = page.save_revision(user=cls.request.user)
            revision.publish(user=cls.request.user)
            cls.num_parent_objects += 1

            if cls.include_descendants:
                for draft_descendant_page in page.get_descendants().not_live().defer_streamfields().specific():
                    if draft_descendant_page.permissions_for_user(cls.request.user).can_publish():
                        revision = draft_descendant_page.save_revision(user=cls.request.user)
                        revision.publish(user=cls.request.user)
                        cls.num_child_objects += 1

    def get_success_message(self):
        if self.num_parent_objects == 1:
            if self.include_descendants:
                if self.num_child_objects == 0:
                    success_message = _("1 page has been published")
                else:
                    success_message = ngettext(
                        "1 page and %(num_child_objects)d child page have been published",
                        "1 page and %(num_child_objects)d child pages have been published",
                        self.num_child_objects
                    ) % {
                        'num_child_objects': self.num_child_objects
                    }
            else:
                success_message = _("1 page has been published")
        else:
            if self.include_descendants:
                if self.num_child_objects == 0:
                    success_message = _("%(num_parent_objects)d pages have been published") % {'num_parent_objects': self.num_parent_objects}
                else:
                    success_message = ngettext(
                        "%(num_parent_objects)d pages and %(num_child_objects)d child page have been published",
                        "%(num_parent_objects)d pages and %(num_child_objects)d child pages have been published",
                        self.num_child_objects
                    ) % {
                        'num_child_objects': self.num_child_objects,
                        'num_parent_objects': self.num_parent_objects
                    }
            else:
                success_message = _("%(num_parent_objects)d pages have been published") % {'num_parent_objects': self.num_parent_objects}
        return success_message


@hooks.register('register_page_bulk_action')
def publish(request):
    return PublishBulkAction(request)
