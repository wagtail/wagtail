# Helper functions for permission handling.
# These check either Django's auth framework, or wagtailcore.GroupCollectionPermission
# depending on whether the Document model is configured to use collections.

from django.db.models import Q

from wagtail.wagtailadmin.utils import user_passes_test
from wagtail.wagtailcore.models import Collection, CollectionMember, GroupCollectionPermission
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


def collections_with_permission_for_user(user, permission_name):
    """
    Return a queryset of collections that this user has the specified permission over,
    taking permission propagation into child selections into account
    """
    if is_using_collections:
        if user.is_superuser:
            return Collection.objects.all()
        else:
            app_label, codename = permission_name.split('.')
            base_paths = Collection.objects.filter(
                group_permissions__group__in=user.groups.all(),
                group_permissions__permission__content_type__app_label=app_label,
                group_permissions__permission__codename=codename
            ).values_list('path', flat=True)

            if base_paths:
                filters = Q(path__startswith=base_paths[0])
                for path in base_paths[1:]:
                    filters = filters | Q(path__startswith=path)
                return Collection.objects.filter(filters)
            else:
                return Collection.objects.none()
    else:
        return Collection.objects.none()


def collections_with_add_permission_for_user(user):
    """
    Return a queryset of collections that this user can add documents to
    """
    return collections_with_permission_for_user(user, 'wagtaildocs.add_document')


def target_collections_for_move(user, document):
    """
    Return a queryset of collections that this user can move the specified document to.
    (It is assumed that the user has edit permission for the document)
    """
    if is_using_collections:
        if user.is_superuser:
            return Collection.objects.all()
        else:
            # user can leave it in its current collection, or move it to one where they
            # have 'add' permission
            return collections_with_add_permission_for_user(user) | Collection.objects.filter(id=document.collection_id)
    else:
        return Collection.objects.none()


def documents_editable_by_user(user):
    """
    Return a queryset of documents editable by the given user
    """
    return Document.objects.filter(
        Q(collection__in=collections_with_permission_for_user(user, 'wagtaildocs.change_document'))
        | Q(collection__in=collections_with_permission_for_user(user, 'wagtaildocs.add_document'), uploaded_by_user=user)
    )
