# Helper functions for permission handling.
# These check either Django's auth framework, or wagtailcore.GroupCollectionPermission
# depending on whether the image model is configured to use collections.

from django.db.models import Q

from wagtail.wagtailadmin.utils import user_passes_test
from wagtail.wagtailcore.models import Collection, CollectionMember, GroupCollectionPermission
from wagtail.wagtailimages.models import get_image_model

Image = get_image_model()
is_using_collections = issubclass(Image, CollectionMember)


def user_has_any_image_permission(user):
    """
    Return true iff user has any image-related permission anywhere in the collections tree.
    """
    if is_using_collections:
        if user.is_superuser:
            return True
        else:
            return GroupCollectionPermission.objects.filter(
                permission__content_type__app_label='wagtailimages',
                permission__codename__in=['add_image', 'change_image'],
                group__in=user.groups.all()
            ).exists()
    else:
        return user.has_perm('wagtailimages.add_image') or user.has_perm('wagtailimages.change_image')


def any_image_permission_required():
    """
    View decorator - the user may only proceed if they have any image-related permission.
    """
    return user_passes_test(user_has_any_image_permission)


def user_has_image_permission(user, permission_name):
    """
    Return true iff user has the specified image permission anywhere in the collections tree.
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


def image_permission_required(permission_name):
    """
    View decorator - the user may only proceed if they have the specified
    image-related permission anywhere in the collections tree.
    """
    def test(user):
        return user_has_image_permission(user, permission_name)

    return user_passes_test(test)


def user_has_permission_on_image(user, permission_name, image):
    """
    Return true iff user has the specified permission on the given image.
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
                collection__in=image.collection.get_ancestors(inclusive=True),
            ).exists()
    else:
        return user.has_perm(permission_name)


def user_can_edit_image(user, image):
    if user_has_permission_on_image(user, 'wagtailimages.change_image', image):
        # user has permission to change image regardless of user
        return True
    elif user_has_permission_on_image(user, 'wagtailimages.add_image', image) and image.uploaded_by_user == user:
        # user has image add permission, which also implicitly provides permission to edit their own images
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
    Return a queryset of collections that this user can add images to
    """
    return collections_with_permission_for_user(user, 'wagtailimages.add_image')


def target_collections_for_move(user, image):
    """
    Return a queryset of collections that this user can move the specified image to.
    (It is assumed that the user has edit permission for the image)
    """
    if is_using_collections:
        if user.is_superuser:
            return Collection.objects.all()
        else:
            # user can leave it in its current collection, or move it to one where they
            # have 'add' permission
            return collections_with_add_permission_for_user(user) | Collection.objects.filter(id=image.collection_id)
    else:
        return Collection.objects.none()


def images_editable_by_user(user):
    """
    Return a queryset of images editable by the given user
    """
    collections_with_change_permission = collections_with_permission_for_user(user, 'wagtailimages.change_image').values_list('id', flat=True)
    collections_with_add_permission = collections_with_permission_for_user(user, 'wagtailimages.add_image').values_list('id', flat=True)
    return Image.objects.filter(
        Q(collection__in=list(collections_with_change_permission))
        | Q(collection__in=list(collections_with_add_permission), uploaded_by_user=user)
    )
