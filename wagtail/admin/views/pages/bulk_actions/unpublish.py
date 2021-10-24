from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.admin.views.pages.bulk_actions.page_bulk_action import PageBulkAction


class UnpublishBulkAction(PageBulkAction):
    display_name = _("Unpublish")
    action_type = "unpublish"
    aria_label = _("Unpublish selected pages")
    template_name = "wagtailadmin/pages/bulk_actions/confirm_bulk_unpublish.html"
    action_priority = 50

    def check_perm(self, page):
        return page.permissions_for_user(self.request.user).can_unpublish()

    def object_context(self, page):
        return {
            **super().object_context(page),
            'live_descendant_count': page.get_descendants().live().count(),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_live_descendants'] = any(map(lambda x: x['live_descendant_count'] > 0, context['items']))
        return context

    def get_execution_context(self):
        return {
            **super().get_execution_context(),
            'permission_checker': self.check_perm,
            'include_descendants': self.cleaned_form.cleaned_data['include_descendants'],
        }

    @classmethod
    def execute_action(cls, objects, include_descendants=False, user=None, permission_checker=None, **kwargs):
        num_parent_objects, num_child_objects = 0, 0
        for page in objects:
            page.unpublish(user=user)
            num_parent_objects += 1

            if include_descendants:
                for live_descendant_page in page.get_descendants().live().defer_streamfields().specific():
                    if user is None or permission_checker(live_descendant_page):
                        live_descendant_page.unpublish()
                        num_child_objects += 1
        return num_parent_objects, num_child_objects

    def get_success_message(self, num_parent_objects, num_child_objects):
        include_descendants = self.cleaned_form.cleaned_data['include_descendants']
        if num_parent_objects == 1:
            if include_descendants:
                if num_child_objects == 0:
                    success_message = _("1 page has been unpublished")
                else:
                    success_message = ngettext(
                        "1 page and %(num_child_objects)d child page have been unpublished",
                        "1 page and %(num_child_objects)d child pages have been unpublished",
                        num_child_objects
                    ) % {
                        'num_child_objects': num_child_objects
                    }
            else:
                success_message = _("1 page has been unpublished")
        else:
            if include_descendants:
                if num_child_objects == 0:
                    success_message = _("%(num_parent_objects)d pages have been unpublished") % {'num_parent_objects': num_parent_objects}
                else:
                    success_message = ngettext(
                        "%(num_parent_objects)d pages and %(num_child_objects)d child page have been unpublished",
                        "%(num_parent_objects)d pages and %(num_child_objects)d child pages have been unpublished",
                        num_child_objects
                    ) % {
                        'num_child_objects': num_child_objects,
                        'num_parent_objects': num_parent_objects
                    }
            else:
                success_message = _("%(num_parent_objects)d pages have been unpublished") % {'num_parent_objects': num_parent_objects}
        return success_message
