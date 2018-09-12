from django import forms
from django.utils import timezone
from django.utils.translation import ugettext as _

from wagtail.core.models import Page

from .auth import *  # NOQA
from .choosers import *  # NOQA
from .collections import *  # NOQA
from .models import *  # NOQA
from .models import WagtailAdminModelForm
from .pages import *  # NOQA
from .search import *  # NOQA
from .view_restrictions import *  # NOQA


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
