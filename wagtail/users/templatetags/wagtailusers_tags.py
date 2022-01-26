import itertools
import re

from django import template

from wagtail.core import hooks


register = template.Library()


@register.inclusion_tag('wagtailusers/groups/includes/formatted_permissions.html')
def format_permissions(permission_bound_field):
    """
        Given a bound field with a queryset of Permission objects - which must be using
        the CheckboxSelectMultiple widget - construct a list of dictionaries for 'objects':

        'objects': [
            {
                'object': name_of_some_content_object,
                'add': checkbox
                'change': checkbox
                'delete': checkbox
                'custom': list_of_checkboxes_for_custom_permissions
            },
        ]

        and a list of other permissions:

        'others': [
            (any_non_add_change_delete_permission, checkbox),
        ]

        (where 'checkbox' is an object with a tag() method that renders the checkbox as HTML;
        this is a BoundWidget on Django >=1.11)

        - and returns a table template formatted with this list.

    """
    permissions = permission_bound_field.field._queryset
    # get a distinct list of the content types that these permissions relate to
    content_type_ids = set(permissions.values_list('content_type_id', flat=True))

    # iterate over permission_bound_field to build a lookup of individual renderable
    # checkbox objects
    # checkbox.data['value'] gives a ModelChoiceIteratorValue
    checkboxes_by_id = {
        int(checkbox.data['value'].value): checkbox
        for checkbox in permission_bound_field
    }

    object_perms = []
    other_perms = []
    custom_perms_exist = False

    for content_type_id in content_type_ids:
        content_perms = permissions.filter(content_type_id=content_type_id)
        content_perms_dict = {}
        custom_perms = []

        if content_perms[0].content_type.name == "admin":
            perm = content_perms[0]
            other_perms.append((perm, checkboxes_by_id[perm.id]))
            continue

        for perm in content_perms:
            content_perms_dict['object'] = perm.content_type.name
            checkbox = checkboxes_by_id[perm.id]
            # identify the three main categories of permission, and assign to
            # the relevant dict key, else bung in the 'other_perms' list
            permission_action = perm.codename.split('_')[0]
            if permission_action in ['add', 'change', 'delete']:
                content_perms_dict[permission_action] = {
                    'perm': perm, 'checkbox': checkbox,
                }
            else:
                custom_perms_exist = True
                custom_perms.append({'perm': perm,
                                     'name': re.sub(f"{perm.content_type.name}$", "", perm.name, flags=re.I).strip(),
                                     'selected': checkbox.data['selected']})

        content_perms_dict['custom'] = custom_perms
        object_perms.append(content_perms_dict)
    return {
        'object_perms': object_perms,
        'other_perms': other_perms,
        'custom_perms_exist': custom_perms_exist
    }


@register.inclusion_tag("wagtailadmin/pages/listing/_buttons.html",
                        takes_context=True)
def user_listing_buttons(context, user):
    button_hooks = hooks.get_hooks('register_user_listing_buttons')
    buttons = sorted(itertools.chain.from_iterable(
        hook(context, user)
        for hook in button_hooks))
    return {'user': user, 'buttons': buttons}
