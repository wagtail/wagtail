import itertools
import re

from django import template

from wagtail import hooks
from wagtail.users.permission_order import CONTENT_TYPE_ORDER

register = template.Library()


@register.inclusion_tag("wagtailusers/groups/includes/formatted_permissions.html")
def format_permissions(permission_bound_field):
    """
    Given a bound field with a queryset of Permission objects - which must be using
    the CheckboxSelectMultiple widget - construct a list of dictionaries for 'objects':

    'objects': [
        {
            'object': name_of_some_content_object,
            'add': checkbox,
            'change': checkbox,
            'delete': checkbox,
            'publish': checkbox,  # only if the model extends DraftStateMixin
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
    # get a distinct and ordered list of the content types that these permissions relate to.
    # relies on Permission model default ordering, dict.fromkeys() retaining that order
    # from the queryset, and the stability of sorted().
    content_type_ids = sorted(
        dict.fromkeys(permissions.values_list("content_type_id", flat=True)),
        key=lambda ct: CONTENT_TYPE_ORDER.get(ct, float("inf")),
    )

    # iterate over permission_bound_field to build a lookup of individual renderable
    # checkbox objects
    # checkbox.data['value'] gives a ModelChoiceIteratorValue
    checkboxes_by_id = {
        int(checkbox.data["value"].value): checkbox
        for checkbox in permission_bound_field
    }

    object_perms = []
    other_perms = []

    # Permissions that are known by Wagtail, to be shown under their own columns.
    # Other permissions will be shown under the "custom permissions" column.
    main_permission_names = ["add", "change", "delete", "publish", "lock", "unlock"]

    # Only show the columns for these permissions if any of the model has them.
    extra_perms_exist = {
        "publish": False,
        "lock": False,
        "unlock": False,
        "custom": False,
    }

    for content_type_id in content_type_ids:
        content_perms = permissions.filter(content_type_id=content_type_id)
        content_perms_dict = {}
        custom_perms = []

        if content_perms[0].content_type.name == "admin":
            perm = content_perms[0]
            other_perms.append((perm, checkboxes_by_id[perm.id]))
            continue

        for perm in content_perms:
            content_perms_dict["object"] = perm.content_type.name
            checkbox = checkboxes_by_id[perm.id]
            # identify the main categories of permission, and assign to
            # the relevant dict key, else bung in the 'custom_perms' list
            permission_action = perm.codename.split("_")[0]
            if permission_action in main_permission_names:
                if permission_action in extra_perms_exist:
                    extra_perms_exist[permission_action] = True
                content_perms_dict[permission_action] = {
                    "perm": perm,
                    "checkbox": checkbox,
                }
            else:
                extra_perms_exist["custom"] = True
                custom_perms.append(
                    {
                        "perm": perm,
                        "name": re.sub(
                            f"{perm.content_type.name}$", "", perm.name, flags=re.I
                        ).strip(),
                        "selected": checkbox.data["selected"],
                    }
                )

        content_perms_dict["custom"] = custom_perms
        object_perms.append(content_perms_dict)
    return {
        "object_perms": object_perms,
        "other_perms": other_perms,
        "extra_perms_exist": extra_perms_exist,
    }


@register.inclusion_tag("wagtailadmin/pages/listing/_buttons.html", takes_context=True)
def user_listing_buttons(context, user):
    button_hooks = hooks.get_hooks("register_user_listing_buttons")
    buttons = sorted(
        itertools.chain.from_iterable(hook(context, user) for hook in button_hooks)
    )
    return {"user": user, "buttons": buttons}
