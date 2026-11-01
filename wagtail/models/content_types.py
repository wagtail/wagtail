import swapper
from django.contrib.contenttypes.models import ContentType


def get_default_page_content_type():
    """
    Returns the content type to use as a default for pages whose content type
    has been deleted.
    """
    Page = swapper.load_model("wagtailcore", "Page")

    return ContentType.objects.get_for_model(Page)
