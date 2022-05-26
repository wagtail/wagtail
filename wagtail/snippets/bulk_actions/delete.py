from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
from wagtail.snippets.permissions import get_permission_name


class DeleteBulkAction(SnippetBulkAction):
    display_name = _("Delete")
    action_type = "delete"
    aria_label = _("Delete selected snippets")
    template_name = "wagtailsnippets/bulk_actions/confirm_bulk_delete.html"
    action_priority = 30
    classes = {"serious"}

    def check_perm(self, snippet):
        if getattr(self, "can_delete_items", None) is None:
            # since snippets permissions are not enforced per object, makes sense to just check once per model request
            self.can_delete_items = self.request.user.has_perm(
                get_permission_name("delete", self.model)
            )
        return self.can_delete_items

    @classmethod
    def execute_action(cls, objects, user=None, **kwargs):
        kwargs["self"].model.objects.filter(
            pk__in=[snippet.pk for snippet in objects]
        ).delete()
        return len(objects), 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        if num_parent_objects == 1:
            return _("%(snippet_type)s '%(instance)s' deleted.") % {
                "snippet_type": capfirst(self.model._meta.verbose_name),
                "instance": self.actionable_objects[0],
            }
        else:
            return ngettext(
                "%(count)d %(snippet_type)s deleted.",
                "%(count)d %(snippet_type)s deleted.",
                num_parent_objects,
            ) % {
                "snippet_type": capfirst(self.model._meta.verbose_name_plural),
                "count": num_parent_objects,
            }
