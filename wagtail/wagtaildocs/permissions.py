# Helper functions for permission handling.
# These check either Django's auth framework, or wagtailcore.GroupCollectionPermission
# depending on whether the Document model is configured to use collections.

from wagtail.wagtailadmin.utils import user_passes_test
from wagtail.wagtailcore.models import CollectionMember, GroupCollectionPermission
from wagtail.wagtaildocs.models import Document

is_using_collections = issubclass(Document, CollectionMember)


def user_has_any_document_permission(user):
    """
    Return true iff user has any document-related permission anywhere in the collections tree.
    """
    if is_using_collections:
        if user.is_superuser:
            return True
        else:
            return GroupCollectionPermission.objects.filter(
                permission__content_type__app_label='wagtaildocs',
                permission__codename__in=['add_document', 'change_document'],
                group__in=user.groups.all()
            ).exists()
    else:
        return user.has_perm('wagtaildocs.add_document') or user.has_perm('wagtaildocs.change_document')


def any_document_permission_required():
    """
    View decorator - the user may only proceed if they have any document-related permission.
    """
    return user_passes_test(user_has_any_document_permission)


def user_has_document_permission(user, permission_name):
    """
    Return true iff user has the specified document permission anywhere in the collections tree.
    """
    if is_using_collections:
        if user.is_superuser:
            return True
        else:
            app_label, codename = permission_name.split('.')
            return GroupCollectionPermission.objects.filter(
                permission__content_type__app_label=app_label,
                permission__codename=codename,
                group__in=user.groups.all()
            ).exists()
    else:
        return user.has_perm(permission_name)


def document_permission_required(permission_name):
    """
    View decorator - the user may only proceed if they have the specified
    document-related permission anywhere in the collections tree.
    """
    def test(user):
        return user_has_document_permission(user, permission_name)

    return user_passes_test(test)


def user_has_permission_on_document(user, permission_name, document):
    """
    Return true iff user has the specified permission on the given document.
    """
    if is_using_collections:
        if user.is_superuser:
            return True
        else:
            app_label, codename = permission_name.split('.')
            return GroupCollectionPermission.objects.filter(
                permission__content_type__app_label=app_label,
                permission__codename=codename,
                group__in=user.groups.all(),
                collection__in=document.collection.get_ancestors(inclusive=True),
            ).exists()
    else:
        return user.has_perm(permission_name)


def user_can_edit_document(user, document):
    if user_has_permission_on_document(user, 'wagtaildocs.change_document', document):
        # user has global permission to change documents
        return True
    elif user_has_permission_on_document(user, 'wagtaildocs.add_document', document) and document.uploaded_by_user == user:
        # user has document add permission, which also implicitly provides permission to edit their own documents
        return True
    else:
        return False
