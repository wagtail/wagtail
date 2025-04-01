from django.contrib.contenttypes.models import ContentType


def get_default_page_content_type():
    """
    Returns the content type to use as a default for pages whose content type
    has been deleted.
    """
    from wagtail.models import Page

    return ContentType.objects.get_for_model(Page)
