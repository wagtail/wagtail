from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from wagtail.admin.forms.pages import PageViewRestrictionForm
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.models import Page, PageViewRestriction
from wagtail.models.view_restrictions import BaseViewRestriction


def set_privacy(request, page_id):
    page = get_object_or_404(Page, id=page_id).specific_deferred
    page_perms = page.permissions_for_user(request.user)
    if not page_perms.can_set_view_restrictions():
        raise PermissionDenied

    restrictions = page.get_view_restrictions().order_by("-page__depth")
    if restrictions:
        if restrictions[0].page.id == page.id:
            restriction = restrictions[0]
            if len(restrictions) > 1:
                restriction_on_ancestor = restrictions[1]
            else:
                restriction_on_ancestor = None
        else:
            restriction = None
            restriction_on_ancestor = restrictions[0]
    else:
        restriction = None
        restriction_on_ancestor = None

    if request.method == "POST":
        form = PageViewRestrictionForm(
            request.POST,
            instance=restriction,
            private_page_options=page.private_page_options,
        )
        if form.is_valid():
            if form.cleaned_data["restriction_type"] == PageViewRestriction.NONE:
                # remove any existing restriction
                if restriction:
                    restriction.delete(user=request.user)
            else:
                restriction = form.save(commit=False)
                restriction.page = page
                restriction.save(user=request.user)
                # Save the groups many-to-many field
                form.save_m2m()

            return render_modal_workflow(
                request,
                None,
                None,
                None,
                json_data={
                    "step": "set_privacy_done",
                    "is_public": (form.cleaned_data["restriction_type"] == "none"),
                },
            )

    else:  # request is a GET
        if restriction:
            form = PageViewRestrictionForm(
                instance=restriction,
                private_page_options=page.private_page_options,
            )

        else:
            # no current view restrictions on this page
            form = PageViewRestrictionForm(
                initial={"restriction_type": "none"},
                private_page_options=page.private_page_options,
            )

        if restriction_on_ancestor:
            ancestor_page_link = format_html(
                '<a href="{url}">{title}</a>',
                url=reverse(
                    "wagtailadmin_pages:edit", args=[restriction_on_ancestor.page_id]
                ),
                title=restriction_on_ancestor.page.specific_deferred.get_admin_display_title(),
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

    if len(page.private_page_options) == 0:
        return render_modal_workflow(
            request,
            "wagtailadmin/page_privacy/no_privacy.html",
            None,
        )
    else:
        return render_modal_workflow(
            request,
            "wagtailadmin/page_privacy/set_privacy.html",
            None,
            {
                "page": page,
                "form": form,
            },
            json_data={"step": "set_privacy"},
        )
