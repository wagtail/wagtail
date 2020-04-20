from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from wagtail.admin import widgets
from wagtail.core.models import Page, PageViewRestriction

from .models import WagtailAdminModelForm
from .view_restrictions import BaseViewRestrictionForm


class CopyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # CopyPage must be passed a 'page' kwarg indicating the page to be copied
        self.page = kwargs.pop('page')
        self.user = kwargs.pop('user', None)
        can_publish = kwargs.pop('can_publish')
        super().__init__(*args, **kwargs)
        self.fields['new_title'] = forms.CharField(initial=self.page.title, label=_("New title"))
        self.fields['new_slug'] = forms.SlugField(initial=self.page.slug, label=_("New slug"))
        self.fields['new_parent_page'] = forms.ModelChoiceField(
            initial=self.page.get_parent(),
            queryset=Page.objects.all(),
            widget=widgets.AdminPageChooser(can_choose_root=True, user_perms='copy_to'),
            label=_("New parent page"),
            help_text=_("This copy will be a child of this given parent page.")
        )
        pages_to_copy = self.page.get_descendants(inclusive=True)
        subpage_count = pages_to_copy.count() - 1
        if subpage_count > 0:
            self.fields['copy_subpages'] = forms.BooleanField(
                required=False, initial=True, label=_("Copy subpages"),
                help_text=ngettext(
                    "This will copy %(count)s subpage.",
                    "This will copy %(count)s subpages.",
                    subpage_count) % {'count': subpage_count})

        if can_publish:
            pages_to_publish_count = pages_to_copy.live().count()
            if pages_to_publish_count > 0:
                # In the specific case that there are no subpages, customise the field label and help text
                if subpage_count == 0:
                    label = _("Publish copied page")
                    help_text = _("This page is live. Would you like to publish its copy as well?")
                else:
                    label = _("Publish copies")
                    help_text = ngettext(
                        "%(count)s of the pages being copied is live. Would you like to publish its copy?",
                        "%(count)s of the pages being copied are live. Would you like to publish their copies?",
                        pages_to_publish_count) % {'count': pages_to_publish_count}

                self.fields['publish_copies'] = forms.BooleanField(
                    required=False, initial=True, label=label, help_text=help_text
                )

    def clean(self):
        cleaned_data = super().clean()

        # Make sure the slug isn't already in use
        slug = cleaned_data.get('new_slug')

        # New parent page given in form or parent of source, if parent_page is empty
        parent_page = cleaned_data.get('new_parent_page') or self.page.get_parent()

        # check if user is allowed to create a page at given location.
        if not parent_page.permissions_for_user(self.user).can_add_subpage():
            self._errors['new_parent_page'] = self.error_class([
                _("You do not have permission to copy to page \"%(page_title)s\"") % {'page_title': parent_page.get_admin_display_title()}
            ])

        # Count the pages with the same slug within the context of our copy's parent page
        if slug and parent_page.get_children().filter(slug=slug).count():
            self._errors['new_slug'] = self.error_class(
                [_("This slug is already in use within the context of its parent page \"%s\"" % parent_page)]
            )
            # The slug is no longer valid, hence remove it from cleaned_data
            del cleaned_data['new_slug']

        # Don't allow recursive copies into self
        if cleaned_data.get('copy_subpages') and (self.page == parent_page or parent_page.is_descendant_of(self.page)):
            self._errors['new_parent_page'] = self.error_class(
                [_("You cannot copy a page into itself when copying subpages")]
            )

        return cleaned_data


class PageViewRestrictionForm(BaseViewRestrictionForm):

    class Meta:
        model = PageViewRestriction
        fields = ('restriction_type', 'password', 'groups')


class WagtailAdminPageForm(WagtailAdminModelForm):

    class Meta:
        # (dealing with Treebeard's tree-related fields that really should have
        # been editable=False)
        exclude = ['content_type', 'path', 'depth', 'numchild']

    def __init__(self, data=None, files=None, parent_page=None, *args, **kwargs):
        super().__init__(data, files, *args, **kwargs)
        self.parent_page = parent_page

    def clean(self):

        cleaned_data = super().clean()
        if 'slug' in self.cleaned_data:
            if not Page._slug_is_available(
                cleaned_data['slug'], self.parent_page, self.instance
            ):
                self.add_error('slug', forms.ValidationError(_("This slug is already in use")))

        # Check scheduled publishing fields
        go_live_at = cleaned_data.get('go_live_at')
        expire_at = cleaned_data.get('expire_at')

        # Go live must be before expire
        if go_live_at and expire_at:
            if go_live_at > expire_at:
                msg = _('Go live date/time must be before expiry date/time')
                self.add_error('go_live_at', forms.ValidationError(msg))
                self.add_error('expire_at', forms.ValidationError(msg))

        # Expire at must be in the future
        if expire_at and expire_at < timezone.now():
            self.add_error('expire_at', forms.ValidationError(_('Expiry date/time must be in the future')))

        # Don't allow an existing first_published_at to be unset by clearing the field
        if 'first_published_at' in cleaned_data and not cleaned_data['first_published_at']:
            del cleaned_data['first_published_at']

        return cleaned_data
