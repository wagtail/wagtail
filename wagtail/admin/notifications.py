import logging

from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q

from wagtail.admin.mail import send_notification
from wagtail.models import (
    COMMENTS_RELATION_NAME,
    Comment,
    CommentReply,
    PageSubscription,
)

logger = logging.getLogger("wagtail.admin")


def send_commenting_notifications(changes, page, editor):
    """
    Sends notifications about any changes to comments to anyone who is subscribed.
    """
    relevant_comment_ids = []
    relevant_comment_ids.extend(comment.pk for comment in changes["resolved_comments"])
    relevant_comment_ids.extend(
        comment.pk for comment, replies in changes["new_replies"]
    )

    # Skip if no changes were made
    # Note: We don't email about edited comments so ignore those here
    if (
        not changes["new_comments"]
        and not changes["deleted_comments"]
        and not changes["resolved_comments"]
        and not changes["new_replies"]
    ):
        return

    # Get global page comment subscribers
    subscribers = PageSubscription.objects.filter(
        page=page, comment_notifications=True
    ).select_related("user")
    global_recipient_users = [
        subscriber.user for subscriber in subscribers if subscriber.user != editor
    ]

    # Get subscribers to individual threads
    replies = CommentReply.objects.filter(comment_id__in=relevant_comment_ids)
    comments = Comment.objects.filter(id__in=relevant_comment_ids)
    thread_users = (
        get_user_model()
        .objects.exclude(pk=editor.pk)
        .exclude(pk__in=subscribers.values_list("user_id", flat=True))
        .filter(
            Q(comment_replies__comment_id__in=relevant_comment_ids)
            | Q(**{("%s__pk__in" % COMMENTS_RELATION_NAME): relevant_comment_ids})
        )
        .prefetch_related(
            Prefetch("comment_replies", queryset=replies),
            Prefetch(COMMENTS_RELATION_NAME, queryset=comments),
        )
    )

    # Skip if no recipients
    if not (global_recipient_users or thread_users):
        return
    thread_users = [
        (
            user,
            set(
                list(user.comment_replies.values_list("comment_id", flat=True))
                + list(
                    getattr(user, COMMENTS_RELATION_NAME).values_list("pk", flat=True)
                )
            ),
        )
        for user in thread_users
    ]
    mailed_users = set()

    for current_user, current_threads in thread_users:
        # We are trying to avoid calling send_notification for each user for performance reasons
        # so group the users receiving the same thread notifications together here
        if current_user in mailed_users:
            continue
        users = [current_user]
        mailed_users.add(current_user)
        for user, threads in thread_users:
            if user not in mailed_users and threads == current_threads:
                users.append(user)
                mailed_users.add(user)
        try:
            send_notification(
                users,
                "updated_comments",
                {
                    "page": page,
                    "editor": editor,
                    "new_comments": [
                        comment
                        for comment in changes["new_comments"]
                        if comment.pk in current_threads
                    ],
                    "resolved_comments": [
                        comment
                        for comment in changes["resolved_comments"]
                        if comment.pk in current_threads
                    ],
                    "deleted_comments": [],
                    "replied_comments": [
                        {
                            "comment": comment,
                            "replies": replies,
                        }
                        for comment, replies in changes["new_replies"]
                        if comment.pk in current_threads
                    ],
                },
            )
        except Exception:
            # We don't want to fail the whole save if notifications fail
            logger.exception("Failed to send comment notifications")

    try:
        send_notification(
            global_recipient_users,
            "updated_comments",
            {
                "page": page,
                "editor": editor,
                "new_comments": changes["new_comments"],
                "resolved_comments": changes["resolved_comments"],
                "deleted_comments": changes["deleted_comments"],
                "replied_comments": [
                    {
                        "comment": comment,
                        "replies": replies,
                    }
                    for comment, replies in changes["new_replies"]
                ],
            },
        )
    except Exception:
        # We don't want to fail the whole save if notifications fail
        logger.exception("Failed to send comment notifications")
