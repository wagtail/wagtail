"""
Base model definitions for validating front-end user access to resources such as pages and
documents. These may be subclassed to accommodate specific models such as Page or Collection,
but the definitions here should remain generic and not depend on the base wagtail.models
module or specific models defined there.
"""

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseViewRestriction(models.Model):
    NONE = "none"
    PASSWORD = "password"
    GROUPS = "groups"
    LOGIN = "login"

    RESTRICTION_CHOICES = (
        (NONE, _("Public")),
        (PASSWORD, _("Private, accessible with a shared password")),
        (LOGIN, _("Private, accessible to any logged-in users")),
        (GROUPS, _("Private, accessible to users in specific groups")),
    )

    restriction_type = models.CharField(max_length=20, choices=RESTRICTION_CHOICES)
    password = models.CharField(
        verbose_name=_("shared password"),
        max_length=255,
        blank=True,
        help_text=_(
            "Shared passwords should not be used to protect sensitive content. Anyone who has this password will be able to view the content."
        ),
    )
    groups = models.ManyToManyField(Group, verbose_name=_("groups"), blank=True)

    def accept_request(self, request):
        if self.restriction_type == BaseViewRestriction.PASSWORD:
            passed_restrictions = request.session.get(
                self.passed_view_restrictions_session_key, []
            )
            if self.id not in passed_restrictions:
                return False

        elif self.restriction_type == BaseViewRestriction.LOGIN:
            if not request.user.is_authenticated:
                return False

        elif self.restriction_type == BaseViewRestriction.GROUPS:
            if not request.user.is_superuser:
                current_user_groups = request.user.groups.all()

                if not any(group in current_user_groups for group in self.groups.all()):
                    return False

        return True

    def mark_as_passed(self, request):
        """
        Update the session data in the request to mark the user as having passed this
        view restriction
        """
        has_existing_session = settings.SESSION_COOKIE_NAME in request.COOKIES
        passed_restrictions = request.session.setdefault(
            self.passed_view_restrictions_session_key, []
        )
        if self.id not in passed_restrictions:
            passed_restrictions.append(self.id)
            request.session[self.passed_view_restrictions_session_key] = (
                passed_restrictions
            )
        if not has_existing_session:
            # if this is a session we've created, set it to expire at the end
            # of the browser session
            request.session.set_expiry(0)

    class Meta:
        abstract = True
        verbose_name = _("view restriction")
        verbose_name_plural = _("view restrictions")
