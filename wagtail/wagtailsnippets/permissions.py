from django.contrib.auth.models import Permission

from wagtail.wagtailsnippets.models import get_snippet_content_types


def user_can_edit_snippet_type(user, content_type):
    """ true if user has any permission related to this content type """
    if user.is_active and user.is_superuser:
        return True

    permission_codenames = content_type.permission_set.values_list('codename', flat=True)
    for codename in permission_codenames:
        permission_name = "%s.%s" % (content_type.app_label, codename)
        if user.has_perm(permission_name):
            return True

    return False


def user_can_edit_snippets(user):
    """ true if user has any permission related to any content type registered as a snippet type """
    snippet_content_types = get_snippet_content_types()
    if user.is_active and user.is_superuser:
        # admin can edit snippets iff any snippet types exist
        return bool(snippet_content_types)

    permissions = Permission.objects.filter(content_type__in=snippet_content_types).select_related('content_type')
    for perm in permissions:
        permission_name = "%s.%s" % (perm.content_type.app_label, perm.codename)
        if user.has_perm(permission_name):
            return True

    return False
