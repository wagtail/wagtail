import warnings
from collections import defaultdict
from typing import TYPE_CHECKING, Optional

from django.db.models import Model
from django.db.models.base import ModelBase

from wagtail import __version__ as WAGTAIL_VERSION
from wagtail.utils.deprecation import RemovedInWagtail219Warning

if TYPE_CHECKING:
    from .options import ModelAdmin, ModelAdminBase


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class RegistryValueError(Exception):
    pass


class ModelAdminRegistry:
    """
    A registry of modeladmin instances, keyed by the ``model`` they represent.
    """

    enforce_model_uniqueness = WAGTAIL_VERSION > "2.19"

    def __init__(self):
        if self.enforce_model_uniqueness:
            self._registry = {}
        else:
            self._registry = defaultdict(list)

    def add(
        self,
        model: ModelBase,
        admin_class: Optional["ModelAdminBase"] = None,
        register_hooks: bool = True,
        **options,
    ) -> "ModelAdmin":
        """
        Adds a modeladmin instance to the registry for the provided ``model``,
        so that other components within Wagta

        If ``admin_class`` is not provided, one will be generated dynamically,
        using ``wagtail.contrib.modeladmin.options.ModelAdmin`` as a base.

        If any additional keyword arguments are provided (for example:
        ``list_display``), they will be used to generate a new ``ModelAdmin``
        class with attribute names and values set accordingly.

        Raises ``RegistryValueError`` when:

        * ``model`` is not a model class
        * ``model`` is an abstract model class
        * ``admin_class`` is something other than ``None`` or a subclass of
          ``wagtail.contrib.modeladmin.options.ModelAdmin``
        """
        from .options import ModelAdmin  # circular imports

        if not isinstance(model, ModelBase):
            raise RegistryValueError(
                "'model' is expected to be a model class, not an instance of "
                f"{type(model)}."
            )

        if model._meta.abstract:
            raise RegistryValueError(
                f"The model {model.__name__} is abstract, so it cannot be "
                "registered."
            )

        if model in self._registry:
            if self.enforce_model_uniqueness:
                raise AlreadyRegistered(
                    f"The model {model.__name__} is already registered."
                )
            else:
                # TODO: To be removed in v2.19
                warnings.warn(
                    "More than one ModelAdmin class was registered for the "
                    f"model {model.__name__}. This option will be removed "
                    "in future versions of Wagtail, and an AlreadyRegistered "
                    "error will raised.",
                    category=RemovedInWagtail219Warning,
                )

        if admin_class is None:
            admin_class = ModelAdmin
        elif not issubclass(admin_class, ModelAdmin):
            raise RegistryValueError(
                "'admin_class' is expected to be a modeladmin subclass, not "
                f"an instance of {type(admin_class)}."
            )

        # The modeladmin class needs to have a `model` attribute value
        # matching the supplied model. If it has something else, updating
        # options should force generation of a new class, even if no other
        # options were provided.
        if getattr(admin_class, "model", None) is not model:
            options["model"] = model

        # Dynamically construct a subclass of admin_class with the
        # desired **options.
        if options:
            options["__module__"] = __name__
            admin_class = type("%sAdmin" % model.__name__, (admin_class,), options)

        # Instantiate the admin class
        modeladmin = admin_class()

        if register_hooks:
            modeladmin.register_with_wagtail()

        # Add the modeladmin instance to the registry
        if self.enforce_model_uniqueness:
            self._registry[model] = modeladmin
        else:
            # TODO: To be removed in v2.19
            self._registry[model].append(modeladmin)
        return modeladmin

    def is_registered(self, model: ModelBase, *, exact: bool = False) -> bool:
        """
        Returns a boolean indicating whether a modeladmin class has be registered
        for the supplied ``model``.

        If ``exact`` is ``False``, a value of ``True`` may also be returned if
        a modeladmin class has been registered for a concrete ancestor of
        ``model``.
        """
        if model in self._registry:
            return True
        if not exact:
            for base in [
                b
                for b in model.__bases__
                if issubclass(b, Model) and not b._meta.abstract
            ]:
                if self.is_registered(model, exact=False):
                    return True
        return False

    def get_modeladmin(self, model: ModelBase, *, exact: bool = False) -> "ModelAdmin":
        """
        Returns the modeladmin instance responsible for administering the
        supplied ``model``.

        If ``exact`` is ``False``, modeladmin classes registered for concrete
        ancestors of ``model`` may be returned if nothing is registered for
        the exact ``model``.

        Raises ``NotRegistered`` if no suitable modeladmin classes are
        registered.
        """
        try:
            if self.enforce_model_uniqueness:
                return self._registry[model]
            else:
                # TODO: To be removed in v2.19
                return self._registry[model][0]
        except KeyError:
            if not exact:
                # Look for a modeladmin class registered for an ancestor
                for base in [
                    b
                    for b in model.__bases__
                    if issubclass(b, Model) and not b._meta.abstract
                ]:
                    try:
                        return self.get_modeladmin(base, exact=False)
                    except NotRegistered:
                        pass
            raise NotRegistered(f"The model {model.__name__} is not registered.")
