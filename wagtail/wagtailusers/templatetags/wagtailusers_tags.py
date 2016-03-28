from __future__ import absolute_import, unicode_literals

from django import template

register = template.Library()


@register.inclusion_tag('wagtailusers/groups/includes/formatted_permissions.html')
def format_permissions(permission_bound_field):
    """
        Given a bound field with a queryset of Permission objects, constructs a
        list of dictionaries for 'objects':

        'objects': [
            {
                'object': name_of_some_content_object,
                'add': (add_permission_for_object, checked_str)
                'change': (change_permission_for_object, checked_str)
                'delete': (delete_permission_for_object, checked_str)
            },
        ]

        and a list of other permissions:

        'others': [
            (any_non_add_change_delete_permission, checked_str),
        ]

        and returns a table template formatted with this list.

    """
    permissions = permission_bound_field.field._queryset
    # get a distinct list of the content types that these permissions relate to
    content_type_ids = set(permissions.values_list('content_type_id', flat=True))
    initial = permission_bound_field.form.initial.get('permissions', [])

    object_perms = []
    other_perms = []

    for content_type_id in content_type_ids:
        content_perms = permissions.filter(content_type_id=content_type_id)
        content_perms_dict = {}
        for perm in content_perms:
            checked = 'checked="checked"' if perm.id in initial else ''
            # identify the three main categories of permission, and assign to
            # the relevant dict key, else bung in the 'other_perms' list
            if perm.codename.split('_')[0] in ['add', 'change', 'delete']:
                content_perms_dict['object'] = perm.content_type.name
                content_perms_dict[perm.codename.split('_')[0]] = (perm, checked)
            else:
                other_perms.append((perm, checked))
        if content_perms_dict:
            object_perms.append(content_perms_dict)
    return {
        'object_perms': object_perms,
        'other_perms': other_perms,
    }
