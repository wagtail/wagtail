from django.db import models

from wagtail.models import AbstractPageViewRestriction


class PageViewRestriction(AbstractPageViewRestriction):
    ADMIN = "admin"
    RESTRICTION_CHOICES = (
        *AbstractPageViewRestriction.RESTRICTION_CHOICES,
        (ADMIN, "Private, accessible to superusers"),
    )
    restriction_type = models.CharField(max_length=20, choices=RESTRICTION_CHOICES)

    def accept_request(self, request):
        if self.restriction_type == PageViewRestriction.ADMIN:
            return request.user.is_superuser
        return super().accept_request(request)
