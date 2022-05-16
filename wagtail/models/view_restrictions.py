"""
Base model definitions for validating front-end user access to resources such as pages and
documents. These may be subclassed to accommodate specific models such as Page or Collection,
but the definitions here should remain generic and not depend on the base wagtail.models
module or specific models defined there.
"""

from typing import Iterator

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _


class BaseViewRestriction(models.Model):
    NONE = "none"
    PASSWORD = "password"
    GROUPS = "groups"
    LOGIN = "login"

    RESTRICTION_CHOICES = (
        (NONE, _("Public")),
        (LOGIN, _("Private, accessible to logged-in users")),
        (PASSWORD, _("Private, accessible with the following password")),
        (GROUPS, _("Private, accessible to users in specific groups")),
    )

    restriction_type = models.CharField(max_length=20, choices=RESTRICTION_CHOICES)
    password = models.CharField(verbose_name=_("password"), max_length=255, blank=True)
    groups = models.ManyToManyField(Group, verbose_name=_("groups"), blank=True)

    @classmethod
    def _get_all_cache_key(cls) -> str:
        return f"__all__.{cls._meta.verbose_name_plural.lower()}"

    @classmethod
    def get_all_queryset(cls) -> QuerySet:
        return cls.objects.all().prefetch_related("groups")

    @classmethod
    def get_all(cls, cache_target=None) -> QuerySet:
        """
        Return all item in descending page path order, and with page and
        group values prefetched.
        """
        cache_key = cls._get_all_cache_key()

        # Return a cached value from the supplied object if available
        value = getattr(cache_target, cache_key, None)
        if value is not None:
            return value

        value = cls.get_all_queryset()

        # Add reference to the supplied `cache_target`
        if cache_target is not None:
            setattr(cache_target, cache_key, value)

        return value

    @classmethod
    def get_all_accepting_user(
        cls,
        user,
        request=None,
        assume_user_authenticated=False,
        assume_passwords_known=False,
    ) -> Iterator["BaseViewRestriction"]:
        """
        Returns all restrictions of this type that the provided ``user`` passes.
        """
        for obj in cls.get_all(request or user):
            if obj.accept_user(
                user, request, assume_user_authenticated, assume_passwords_known
            ):
                yield obj

    @classmethod
    def get_permitted_objects_q(
        cls,
        user,
        request=None,
        assume_user_authenticated=False,
        assume_passwords_known=False,
    ) -> Q:
        """
        Returns a ``Q`` object that can be used to filter a queryset of objects
        to only include items the provided ``user`` is permitted to access, based
        on all saved restrictions of this type.
        """
        accepting_restrictions = tuple(
            cls.get_all_accepting_user(
                user, request, assume_user_authenticated, assume_passwords_known
            )
        )

        inclusive_q = Q()
        for obj in accepting_restrictions:
            inclusive_q |= obj.get_affected_objects_q

        restrictive_q = Q()
        for obj in cls.get_all(request or user):
            if obj not in accepting_restrictions:
                restrictive_q &= obj.get_affected_objects_with_conflicts_q(
                    accepting_restrictions
                )

        return inclusive_q & ~restrictive_q

    def get_affected_objects_q(self) -> Q:
        """
        Returns a ``Q`` object that can be used to filter a queryset of
        objects to only include those affected by this restriction.
        Must be overridden for each subclass.
        """
        raise NotImplementedError

    def get_affected_objects_with_conflicts_q(self, conflicting_restrictions) -> Q:
        """
        Similar to ``get_affected_objects_q()``, but returns a more complex ``Q``
        that excludes content affected by ``conflicting_restrictions`` (an iterable
        of restrictions of the same type) if they happen to be applied to a
        decendant node in the page (or collection) tree.
        Utilises ``get_affected_objects_q()``, so shouldn't need overriding on
        subclasses.
        """
        q = self.get_affected_objects_q()
        for obj in conflicting_restrictions:
            if obj.is_descendant_of(self):
                q &= ~obj.get_affected_objects_q()
        return q

    def is_descendant_of(self, other: "BaseViewRestriction") -> bool:
        """
        Returns a boolean indicating whether this object is a descandant
        of another instance (based on where in the tree the content is applied).
        """
        raise False

    def accept_request(self, request: HttpRequest) -> bool:
        return self.accept_user(request.user, request)

    def accept_user(
        self,
        user,
        request: HttpRequest = None,
        assume_user_authenticated: bool = False,
        assume_password_known: bool = False,
    ) -> bool:
        """
        Return a boolean indicating whether the supplied ``user`` passes the restriction.
        ``request`` will typically be a ``HttpRequest`` instance representing a request
        being made by ``user``. However, in contexts where another user is making the
        request or where there is no request at all, any mutable object capable of
        supporting ad hoc attribute assignment can be provided to improve efficiency when
        calling the method more than once.

        By default, restrictions requiring a user to be authenticated will return
        ``False`` unless the ``user`` is indeed authenticated. The method can be called
        with ``assume_user_authenticated=True`` to instead make such restrictions always
        return ``True``.

        By default, restrictions requiring a password return ``False`` unless there is
        evidence of the user successfully passing the restriction (only works when ``user``
        and ``request.user`` are the same user). The method can be called with
        ``assume_password_known=True`` to make such restrictions always return ``True``.
        """
        if self.restriction_type == self.NONE:
            return True

        if self.restriction_type == self.LOGIN:
            if not user.is_active:
                return False
            if assume_user_authenticated:
                return True
            if request and getattr(request, "user", None) == user:
                return user.is_authenticated
            return False

        if self.restriction_type == self.PASSWORD:
            if not user.is_active:
                return False
            if assume_password_known:
                return True
            if request and getattr(request, "user", None) == user:
                passed_restrictions = request.session.get(
                    self.passed_view_restrictions_session_key, []
                )
                return self.id in passed_restrictions
            return False

        if self.restriction_type == self.GROUPS:
            if not user.is_active:
                return False
            if user.is_superuser:
                return True
            user_groups = user.groups.all()
            for group in self.groups.all():
                if group in user_groups:
                    return True
        return False

    def mark_as_passed(self, request: HttpRequest) -> None:
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
            request.session[
                self.passed_view_restrictions_session_key
            ] = passed_restrictions
        if not has_existing_session:
            # if this is a session we've created, set it to expire at the end
            # of the browser session
            request.session.set_expiry(0)

    class Meta:
        abstract = True
        verbose_name = _("view restriction")
        verbose_name_plural = _("view restrictions")
