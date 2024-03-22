from django.contrib.admin.utils import quote
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.views import View

from wagtail.admin.forms.pages import ParentChooserForm
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from wagtail.models import Page
from wagtail.permissions import page_permission_policy


class ChooseParentView(WagtailAdminTemplateMixin, View):
    template_name = "wagtailadmin/pages/choose_parent.html"
    model = Page
    index_url_name = None
    _show_breadcrumbs = True

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

    def get_form(self, request):
        parents = self.get_valid_parent_pages(request.user)
        return ParentChooserForm(parents, request.POST or None)

    def get_breadcrumbs_items(self):
        items = []
        if self.index_url_name:
            items.append(
                {
                    "url": reverse(self.index_url_name),
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        items.append(
            {
                "url": "",
                "label": _("Choose parent: %(model_name)s")
                % {"model_name": capfirst(self.model._meta.verbose_name)},
            }
        )

        return self.breadcrumbs_items + items

    def get(self, request, *args, **kwargs):
        form = self.get_form(request)
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        form = self.get_form(request)
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        opts = self.model._meta

        parent_id = quote(form.cleaned_data["parent_page"].pk)
        return redirect(
            "wagtailadmin_pages:add", opts.app_label, opts.model_name, parent_id
        )

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
