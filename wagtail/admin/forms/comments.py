from django.forms import ValidationError
from django.forms.formsets import DELETION_FIELD_NAME
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

    def clean(self):
        cleaned_data = super().clean()
        user = self.user

        if not self.instance.pk:
            self.instance.user = user
        elif self.instance.user != user:
            # trying to edit someone else's comment
            if any(field for field in self.changed_data if field != DELETION_FIELD_NAME):
                # users can delete each other's base comments, as this is just the "resolve" action
                self.add_error(None, ValidationError(_("You cannot edit another user's comment.")))

        return cleaned_data
