from typing import TYPE_CHECKING, Optional, Union

import django
from django.db.models import Model
from django.db.models.base import ModelBase

from .registry_class import (  # noqa
    AlreadyRegistered,
    ModelAdminRegistry,
    NotRegistered,
    RegistryValueError,
)

if TYPE_CHECKING:
    from .options import ModelAdmin, ModelAdminBase, ModelAdminGroupBase

if django.VERSION >= (3, 2):
    # The declaration is only needed for older Django versions
    pass
else:
    default_app_config = "wagtail.contrib.modeladmin.apps.WagtailModelAdminAppConfig"


_registry = ModelAdminRegistry()


def is_registered(model: ModelBase, *, exact=False) -> bool:
    """
    Returns a boolean indicating whether a modeladmin class has be registered
    for the supplied ``model``.

    If ``exact`` is ``False``, a value of ``True`` may also be returned if
    a modeladmin class has been registered for a concrete ancestor of
    ``model``.
    """
    return _registry.is_registered(model, exact=exact)


def get_modeladmin(model: ModelBase, *, exact=False) -> "ModelAdmin":
    """
    Returns a modeladmin instance responsible for administering the
    supplied ``model``.

    If ``exact`` is ``False``, an instance of a modeladmin class registered
    for a concrete ancestor of ``model`` may be returned if nothing is
    registered for the exact ``model``.

    Raises ``wagtail.contrib.modeladmin.NotRegistered`` if no suitable
    modeladmin classes are registered.
    """
    return _registry.get_modeladmin(model, exact=exact)


def register(
    klass: Union[ModelBase, ModelAdminBase, ModelAdminGroupBase],
    *,
    admin_class: Optional[Union[ModelAdminBase, ModelAdminGroupBase]] = None,
    **options,
):
    """
    Function for registering ``Model``, ``ModelAdmin`` or ``ModelAdminGroup``
    classes with the ``wagtail.contrib.modeladmin`` app.
    """
    from .options import ModelAdmin, ModelAdminGroup  # avoid circular imports

    if issubclass(klass, Model):
        _registry.add(klass, admin_class, **options)
        return klass

    if issubclass(klass, ModelAdmin):
        _registry.add(klass.model, klass, **options)
        return klass

    if issubclass(klass, ModelAdminGroup):
        admin_group = klass()
        # Register each sub-item separately, but avoid calling
        # register_with_wagtail() for each
        for item in admin_group.items:
            if issubclass(item, ModelAdmin):
                instance = _registry.add(item.model, item, register_hooks=False)
                instance.parent = admin_group
            else:
                # item does not belong in the registry, but must still be
                # instantiated
                instance = item()
            admin_group.modeladmin_instances.append(instance)

        # Allow admin_group to register urls, permissions and menu items
        admin_group.register_with_wagtail()
        return klass

    raise RegistryValueError(
        "Only Model, ModelAdmin and ModelAdminGroup classes can be "
        f"registered with modeladmin. {klass} is neither of these."
    )
