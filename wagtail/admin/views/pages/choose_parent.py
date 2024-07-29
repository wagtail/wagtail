from django.contrib.admin.utils import quote
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import FormView

from wagtail.admin.forms.pages import ParentChooserForm
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from wagtail.models import Page
from wagtail.permissions import page_permission_policy


class ChooseParentView(WagtailAdminTemplateMixin, FormView):
    template_name = "wagtailadmin/pages/choose_parent.html"
    model = Page
    index_url_name = None
    page_title = gettext_lazy("Choose parent")

    def get_valid_parent_pages(self, user):
        """
        Identifies possible parent pages for the current user by first looking
        at allowed_parent_page_models() on self.model to limit options to the
        correct type of page, then checking permissions on those individual
        pages to make sure we have permission to add a subpage to it.
        """
        # Get queryset of pages where this page type can be added
        allowed_parent_page_content_types = list(
            ContentType.objects.get_for_models(
                *self.model.allowed_parent_page_models()
            ).values()
        )
        allowed_parent_pages = Page.objects.filter(
            content_type__in=allowed_parent_page_content_types
        )

        # Get queryset of pages where the user has permission to add subpages
        if user.is_superuser:
            pages_where_user_can_add = Page.objects.all()
        else:
            pages_where_user_can_add = Page.objects.none()

            perms = {
                perm
                for perm in page_permission_policy.get_cached_permissions_for_user(user)
                if perm.permission.codename == "add_page"
            }

            for perm in perms:
                # user has add permission on any subpage of perm.page
                # (including perm.page itself)
                pages_where_user_can_add |= Page.objects.descendant_of(
                    perm.page, inclusive=True
                )

        # Combine them
        return allowed_parent_pages & pages_where_user_can_add

    def get(self, request, *args, **kwargs):
        parents = self.get_valid_parent_pages(request.user)

        # Only fetch the IDs for the first two parents to check if there's only
        # one valid parent, and if so, redirect to the add page view with that
        # parent pre-selected
        parent_ids = parents.values_list("pk", flat=True)[:2]
        if len(parent_ids) == 1:
            parent_id = quote(parent_ids[0])
            model_opts = self.model._meta
            return redirect(
                "wagtailadmin_pages:add",
                model_opts.app_label,
                model_opts.model_name,
                parent_id,
            )

        # The page can be added in multiple places, so proceed with rendering
        # the view's form so that the parent can be specified
        return super().get(request, *args, **kwargs)

    def get_form(self):
        if self.request.method == "POST":
            return ParentChooserForm(self.model, self.request.user, self.request.POST)
        return ParentChooserForm(self.model, self.request.user)

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    def get_breadcrumbs_items(self):
        items = []
        index_url = self.get_index_url()
        if index_url:
            items.append(
                {
                    "url": index_url,
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        items.append(
            {
                "url": "",
                "label": self.get_page_title(),
                "sublabel": self.get_page_subtitle(),
            }
        )

        return self.breadcrumbs_items + items

    def get_page_subtitle(self):
        return self.model.get_verbose_name()

    @cached_property
    def submit_button_label(self):
        return _("Create a new %(model_name)s") % {
            "model_name": self.model._meta.verbose_name,
        }

    def form_valid(self, form):
        model_opts = self.model._meta
        parent_id = quote(form.cleaned_data["parent_page"].pk)
        return redirect(
            "wagtailadmin_pages:add",
            model_opts.app_label,
            model_opts.model_name,
            parent_id,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["media"] = context["form"].media
        context["submit_button_label"] = self.submit_button_label
        return context
