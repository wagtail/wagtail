from wagtail.management.commands.publish_scheduled import (
    Command as PublishScheduledCommand,
)


class Command(PublishScheduledCommand):
    """
    Alias for the publish_scheduled management command for backwards-compatibility.
    """
