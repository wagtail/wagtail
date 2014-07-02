from django import template

register = template.Library()

@register.inclusion_tag('wagtailusers/formatted_permissions.html')
def format_permissions(permission_bound_field):
    """
        Given a bound field with a queryset of Permission objects, constructs a
        list of dictionaries:

        [
            {
                'object': name_of_some_content_object,
                'add': (add_permission_for_object, checked_str)
                'change': (change_permission_for_object, checked_str)
                'delete': (delete_permission_for_object, checked_str)
                'others': [
                              (any_other_permission_for_object, checked_str),
                          ]
            },
        ]

        and returns a table template formatted with this list.

    """
    permissions = permission_bound_field.field._queryset
    # get a distinct list of the content types that these permissions relate to
    content_type_ids = set(permissions.values_list('content_type_id', flat=True))
    initial = permission_bound_field.form.initial['permissions']

    perms_array = []
    for content_type_id in content_type_ids:
        content_perms = permissions.filter(content_type_id=content_type_id)
        content_perms_dict = {
            'others': []
        }
        for perm in content_perms:
            content_perms_dict['object'] = perm.content_type.name
            checked = 'checked="checked"' if perm.id in initial else ''
            # identify the three main categories of permission, or bung in
            # 'others' list
            if perm.codename.split('_')[0] in ['add', 'change', 'delete']:
                content_perms_dict[perm.codename.split('_')[0]] = (perm, checked)
            else:
                content_perms_dict['others'].append((perm, checked))
        perms_array.append(content_perms_dict)
    return {
        'perms_array': perms_array,
        }
