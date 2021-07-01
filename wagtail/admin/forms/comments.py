from django.forms import BooleanField, ValidationError
from django.utils.timezone import now
from django.utils.translation import gettext as _

from .models import WagtailAdminModelForm


class CommentReplyForm(WagtailAdminModelForm):
    user = None

    class Meta:
        fields = ('text',)

    def clean(self):
        cleaned_data = super().clean()
        user = self.user

        if not self.instance.pk:
            self.instance.user = user
        elif self.instance.user != user:
            # trying to edit someone else's comment reply
            if any(field for field in self.changed_data):
                # includes DELETION_FIELD_NAME, as users cannot delete each other's individual comment replies
                # if deleting a whole thread, this should be done by deleting the parent Comment instead
                self.add_error(None, ValidationError(_("You cannot edit another user's comment.")))
        return cleaned_data


class CommentForm(WagtailAdminModelForm):
    """
    This is designed to be subclassed and have the user overidden to enable user-based validation within the edit handler system
    """
    user = None

    resolved = BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        user = self.user

        if not self.instance.pk:
            self.instance.user = user
        elif self.instance.user != user:
            # trying to edit someone else's comment
            if any(field for field in self.changed_data if field not in ['resolved', 'position']):
                # users can resolve each other's base comments and change their positions within a field
                self.add_error(None, ValidationError(_("You cannot edit another user's comment.")))
        return cleaned_data

    def save(self, *args, **kwargs):
        if self.cleaned_data.get('resolved', False):
            if not getattr(self.instance, 'resolved_at'):
                self.instance.resolved_at = now()
                self.instance.resolved_by = self.user
        else:
            self.instance.resolved_by = None
            self.instance.resolved_at = None
        return super().save(*args, **kwargs)
