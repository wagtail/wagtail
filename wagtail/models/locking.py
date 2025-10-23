from django.conf import settings
from django.core import checks
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.locks import BasicLock

from .revisions import RevisionMixin


class LockableMixin(models.Model):
    locked = models.BooleanField(
        verbose_name=_("locked"), default=False, editable=False
    )
    locked_at = models.DateTimeField(
        verbose_name=_("locked at"), null=True, editable=False
    )
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("locked by"),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="locked_%(class)ss",
    )
    locked_by.wagtail_reference_index_ignore = True

    class Meta:
        abstract = True

    @classmethod
    def check(cls, **kwargs):
        return [
            *super().check(**kwargs),
            *cls._check_revision_mixin(),
        ]

    @classmethod
    def _check_revision_mixin(cls):
        mro = cls.mro()
        error = checks.Error(
            "LockableMixin must be applied before RevisionMixin.",
            hint="Move LockableMixin in the model's base classes before RevisionMixin.",
            obj=cls,
            id="wagtailcore.E005",
        )

        try:
            if mro.index(RevisionMixin) < mro.index(LockableMixin):
                return [error]
        except ValueError:
            # LockableMixin can be used without RevisionMixin.
            return []

        return []

    def with_content_json(self, content):
        """
        Similar to :meth:`RevisionMixin.with_content_json`,
        but with the following fields also preserved:

        * ``locked``
        * ``locked_at``
        * ``locked_by``
        """
        obj = super().with_content_json(content)

        # Ensure other values that are meaningful for the object as a whole (rather than
        # to a specific revision) are preserved
        obj.locked = self.locked
        obj.locked_at = self.locked_at
        obj.locked_by = self.locked_by

        return obj

    def get_lock(self):
        """
        Returns a sub-class of ``BaseLock`` if the instance is locked, otherwise ``None``.
        """
        if self.locked:
            return BasicLock(self)
