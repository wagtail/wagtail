from django import forms
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from wagtail.models import GroupSitePermission, Site


class SiteSwitchForm(forms.Form):
    site = forms.ChoiceField(
        choices=[],
        widget=forms.Select(
            attrs={
                "data-controller": "w-action",
                "data-action": "change->w-action#redirect",
            }
        ),
    )

    def __init__(self, current_site, model, sites, **kwargs):
        initial_data = {"site": self.get_change_url(current_site, model)}
        super().__init__(initial=initial_data, **kwargs)
        self.fields["site"].choices = [
            (
                self.get_change_url(site, model),
                (
                    site.hostname + " [{}]".format(_("default"))
                    if site.is_default_site
                    else site.hostname
                ),
            )
            for site in sites
        ]

    @classmethod
    def get_change_url(cls, site, model):
        return reverse(
            "wagtailsettings:edit",
            args=[model._meta.app_label, model._meta.model_name, site.pk],
        )


class SitePermissionForm(forms.Form):
    """
    A form to be displayed as a panel on the group edit page, to select which sites a group
    can edit settings for. Should be subclassed to provide a `settings_model` attribute that
    specifies the model that the permissions apply to.
    """

    template_name = "wagtailsettings/permissions/includes/site_permission_form.html"

    sites = forms.ModelMultipleChoiceField(
        queryset=Site.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Sites"),
    )

    def __init__(self, *args, instance, **kwargs):
        if not kwargs.get("prefix"):
            kwargs["prefix"] = (
                f"{self.settings_model._meta.app_label}_{self.settings_model._meta.model_name}_site_permissions"
            )

        content_type = ContentType.objects.get_for_model(self.settings_model)
        permission_codename = get_permission_codename(
            "change", self.settings_model._meta
        )
        self.permission = Permission.objects.get(
            content_type=content_type, codename=permission_codename
        )

        self.instance = instance
        if instance and instance.pk is not None:
            # If the instance already exists, prepopulate the sites field with the sites
            # that the group has permission for.
            kwargs["initial"] = {
                "sites": [
                    permission.site
                    for permission in self.get_existing_permissions().select_related(
                        "site"
                    )
                ]
            }
        super().__init__(*args, **kwargs)

    def get_existing_permissions(self):
        return GroupSitePermission.objects.filter(
            group=self.instance, permission=self.permission
        )

    def as_admin_panel(self):
        return render_to_string(
            self.template_name,
            {
                "heading": capfirst(
                    gettext("%(model)s permissions")
                    % {"model": self.settings_model._meta.verbose_name}
                ),
                "form": self,
                "panel_id": f"{self.settings_model._meta.label_lower.replace('.', '-')}-permissions",
            },
        )

    def save(self):
        existing_site_ids = set(
            self.get_existing_permissions().values_list("site_id", flat=True)
        )
        new_site_ids = set(self.cleaned_data["sites"].values_list("id", flat=True))

        # Determine which sites to add and which to remove
        sites_to_add = new_site_ids - existing_site_ids
        sites_to_remove = existing_site_ids - new_site_ids

        # Add new sites
        for site_id in sites_to_add:
            GroupSitePermission.objects.get_or_create(
                group=self.instance, site_id=site_id, permission=self.permission
            )

        # Remove old sites
        GroupSitePermission.objects.filter(
            group=self.instance, site_id__in=sites_to_remove, permission=self.permission
        ).delete()
