from django import forms
from django.http import Http404
from django.utils.translation import ngettext

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.admin.views.pages.search import page_filter_search
from wagtail.models import Page


class DefaultPageForm(forms.Form):
    include_descendants = forms.BooleanField(required=False)


class PageBulkAction(BulkAction):
    models = [Page]

    @classmethod
    def get_queryset(cls, model, object_ids):
        # Use specific page instances so that custom overrides such as
        # permissions_for_user() on specific page models are respected
        # without relying on the auto-dispatch in Page.permissions_for_user().
        pages = Page.objects.filter(pk__in=object_ids).specific(defer=True)
        if not pages:
            raise Http404("No Page matches the given query.")
        return list(pages)

    form_class = DefaultPageForm

    def get_all_objects_in_listing_query(self, parent_id):
        listing_objects = self.model.objects.all()

        q = None
        if "q" in self.request.GET:
            q = self.request.GET.get("q", "")

        if parent_id is not None:
            listing_objects = listing_objects.get(id=parent_id)
            # If we're searching, include the descendants as well.
            # Otherwise, just include the direct children.
            if q:
                listing_objects = listing_objects.get_descendants()
            else:
                listing_objects = listing_objects.get_children()

        listing_objects = listing_objects.values_list("pk", flat=True)

        if q:
            listing_objects = page_filter_search(q, listing_objects)[0].results()

        return listing_objects

    def object_context(self, obj):
        context = super().object_context(obj)
        # Make 'item' into the specific instance, so that custom get_admin_display_title methods are respected
        context["item"] = context["item"].specific_deferred
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items_with_no_access"] = [
            {
                "item": page,
                "can_edit": page.permissions_for_user(self.request.user).can_edit(),
            }
            for page in context["items_with_no_access"]
        ]
        return context

    def get_execution_context(self):
        return {"user": self.request.user}

    def get_parent_page_text(self, num_parent_objects):
        # Translators: This appears within a message such as "2 pages and 3 child pages have been published"
        return ngettext(
            "%(num_parent_objects)d page",
            "%(num_parent_objects)d pages",
            num_parent_objects,
        ) % {"num_parent_objects": num_parent_objects}

    def get_child_page_text(self, num_child_objects):
        # Translators: This appears within a message such as "2 pages and 3 child pages have been published"
        return ngettext(
            "%(num_child_objects)d child page",
            "%(num_child_objects)d child pages",
            num_child_objects,
        ) % {"num_child_objects": num_child_objects}
