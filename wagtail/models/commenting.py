from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.logging import log


COMMENTS_RELATION_NAME = getattr(settings, 'WAGTAIL_COMMENTS_RELATION_NAME', 'wagtail_admin_comments')


class Comment(ClusterableModel):
    """
    A comment on a field, or a field within a streamfield block
    """
    page = ParentalKey('Page', on_delete=models.CASCADE, related_name=COMMENTS_RELATION_NAME)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name=COMMENTS_RELATION_NAME)
    text = models.TextField()

    contentpath = models.TextField()
    # This stores the field or field within a streamfield block that the comment is applied on, in the form: 'field', or 'field.block_id.field'
    # This must be unchanging across all revisions, so we will not support (current-format) ListBlock or the contents of InlinePanels initially.

    position = models.TextField(blank=True)
    # This stores the position within a field, to be interpreted by the field's frontend widget. It may change between revisions

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    revision_created = models.ForeignKey('PageRevision', on_delete=models.CASCADE, related_name='created_comments', null=True, blank=True)

    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='comments_resolved',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')

    def __str__(self):
        return "Comment on Page '{0}', left by {1}: '{2}'".format(self.page, self.user, self.text)

    def save(self, update_position=False, **kwargs):
        # Don't save the position unless specifically instructed to, as the position will normally be retrieved from the revision
        update_fields = kwargs.pop('update_fields', None)
        if not update_position and (not update_fields or 'position' not in update_fields):
            if self.id:
                # The instance is already saved; we can use `update_fields`
                update_fields = update_fields if update_fields else self._meta.get_fields()
                update_fields = [field.name for field in update_fields if field.name not in {'position', 'id'}]
            else:
                # This is a new instance, we have to preserve and then restore the position via a variable
                position = self.position
                result = super().save(**kwargs)
                self.position = position
                return result
        return super().save(update_fields=update_fields, **kwargs)

    def _log(self, action, page_revision=None, user=None):
        log(
            instance=self.page,
            action=action,
            user=user,
            revision=page_revision,
            data={
                'comment': {
                    'id': self.pk,
                    'contentpath': self.contentpath,
                    'text': self.text,
                }
            }
        )

    def log_create(self, **kwargs):
        self._log('wagtail.comments.create', **kwargs)

    def log_edit(self, **kwargs):
        self._log('wagtail.comments.edit', **kwargs)

    def log_resolve(self, **kwargs):
        self._log('wagtail.comments.resolve', **kwargs)

    def log_delete(self, **kwargs):
        self._log('wagtail.comments.delete', **kwargs)


class CommentReply(models.Model):
    comment = ParentalKey(Comment, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('comment reply')
        verbose_name_plural = _('comment replies')

    def __str__(self):
        return "CommentReply left by '{0}': '{1}'".format(self.user, self.text)

    def _log(self, action, page_revision=None, user=None):
        log(
            instance=self.comment.page,
            action=action,
            user=user,
            revision=page_revision,
            data={
                'comment': {
                    'id': self.comment.pk,
                    'contentpath': self.comment.contentpath,
                    'text': self.comment.text,
                },
                'reply': {
                    'id': self.pk,
                    'text': self.text,
                }
            }
        )

    def log_create(self, **kwargs):
        self._log('wagtail.comments.create_reply', **kwargs)

    def log_edit(self, **kwargs):
        self._log('wagtail.comments.edit_reply', **kwargs)

    def log_delete(self, **kwargs):
        self._log('wagtail.comments.delete_reply', **kwargs)


class PageSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='page_subscriptions')
    page = models.ForeignKey('Page', on_delete=models.CASCADE, related_name='subscribers')

    comment_notifications = models.BooleanField()

    class Meta:
        unique_together = [
            ('page', 'user'),
        ]
