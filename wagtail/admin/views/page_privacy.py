from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import ModelFormMixin, ProcessFormView

from wagtail.admin.forms.pages import PageViewRestrictionForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.models import Page, PageViewRestriction
from wagtail.models.view_restrictions import BaseViewRestriction


class SetPrivacyView(ModelFormMixin, ProcessFormView):
    form_class = PageViewRestrictionForm

    def dispatch(self, request, page_id, *args, **kwargs):
        self.page = get_object_or_404(Page, id=page_id).specific_deferred
        page_perms = self.page.permissions_for_user(request.user)
        if not page_perms.can_set_view_restrictions():
            raise PermissionDenied

        restrictions = self.page.get_view_restrictions().order_by("-page__depth")
        if restrictions:
            if restrictions[0].page.id == self.page.id:
                self.restriction = restrictions[0]
                if len(restrictions) > 1:
                    self.restriction_on_ancestor = restrictions[1]
                else:
                    self.restriction_on_ancestor = None
            else:
                self.restriction = None
                self.restriction_on_ancestor = restrictions[0]
        else:
            self.restriction = None
            self.restriction_on_ancestor = None

        self.object = self.restriction

        return super().dispatch(request, page_id, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.restriction_on_ancestor:
            ancestor_page_link = format_html(
                '<a href="{url}">{title}</a>',
                url=reverse(
                    "wagtailadmin_pages:edit",
                    args=[self.restriction_on_ancestor.page_id],
                ),
                title=self.restriction_on_ancestor.page.specific_deferred.get_admin_display_title(),
            )
            inherit_from_parent_choice = (
                BaseViewRestriction.NONE,
                format_html(
                    "<span>{}</span>",
                    mark_safe(
                        _(
                            "Privacy is inherited from the ancestor page - %(ancestor_page)s"
                        )
                        % {"ancestor_page": ancestor_page_link}
                    ),
                ),
            )
            form.fields["restriction_type"].choices = [
                inherit_from_parent_choice
            ] + list(form.fields["restriction_type"].choices[1:])

        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["private_page_options"] = self.page.private_page_options
        return kwargs

    def get_initial(self):
        if not self.restriction:
            return {"restriction_type": "none"}
        return super().get_initial()

    def form_valid(self, form):
        if form.cleaned_data["restriction_type"] == PageViewRestriction.NONE:
            # remove any existing restriction
            if self.restriction:
                self.restriction.delete(user=self.request.user)
        else:
            restriction = form.save(commit=False)
            restriction.page = self.page
            restriction.save(user=self.request.user)
            # Save the groups many-to-many field
            form.save_m2m()

        return render_modal_workflow(
            self.request,
            None,
            None,
            None,
            json_data={
                "step": "set_privacy_done",
                "is_public": (form.cleaned_data["restriction_type"] == "none"),
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "action_url": reverse(
                    "wagtailadmin_pages:set_privacy", args=(self.page.pk,)
                ),
                "object": self.page,
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        if len(self.page.private_page_options) == 0:
            return render_modal_workflow(
                self.request,
                "wagtailadmin/page_privacy/no_privacy.html",
                None,
            )
        return render_modal_workflow(
            self.request,
            "wagtailadmin/shared/set_privacy.html",
            template_vars=context,
            json_data={"step": "set_privacy"},
            **response_kwargs,
        )
