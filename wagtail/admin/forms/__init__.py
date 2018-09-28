from importlib import import_module
import sys
import warnings

from wagtail.utils.deprecation import RemovedInWagtail25Warning

# definitions which are not being deprecated from wagtail.admin.forms
from .models import (  # NOQA
    FORM_FIELD_OVERRIDES, DIRECT_FORM_FIELD_OVERRIDES, formfield_for_dbfield, WagtailAdminModelFormMetaclass, WagtailAdminModelForm
)
from .pages import WagtailAdminPageForm  # NOQA


# Names previously defined here which now exist in submodules of wagtail.admin.forms:
#
# We want these to be available in this module during deprecation, but can't simply do
# `from .auth import *` or similar as this is susceptible to circular imports when importing
# any submodule (see https://github.com/wagtail/wagtail/issues/4515). As a workaround, we
# fiddle this module's definition in sys.modules to be an object with a custom __getattr__
# method that intercepts accesses to these names and lazily imports them while also
# producing a deprecation warning.

MOVED_DEFINITIONS = {
    'LoginForm': 'wagtail.admin.forms.auth',
    'PasswordResetForm': 'wagtail.admin.forms.auth',

    'URLOrAbsolutePathValidator': 'wagtail.admin.forms.choosers',
    'URLOrAbsolutePathField': 'wagtail.admin.forms.choosers',
    'ExternalLinkChooserForm': 'wagtail.admin.forms.choosers',
    'EmailLinkChooserForm': 'wagtail.admin.forms.choosers',

    'CollectionViewRestrictionForm': 'wagtail.admin.forms.collections',
    'CollectionForm': 'wagtail.admin.forms.collections',
    'BaseCollectionMemberForm': 'wagtail.admin.forms.collections',
    'BaseGroupCollectionMemberPermissionFormSet': 'wagtail.admin.forms.collections',
    'collection_member_permission_formset_factory': 'wagtail.admin.forms.collections',

    'CopyForm': 'wagtail.admin.forms.pages',
    'PageViewRestrictionForm': 'wagtail.admin.forms.pages',

    'SearchForm': 'wagtail.admin.forms.search',

    'BaseViewRestrictionForm': 'wagtail.admin.forms.view_restrictions',
}


class MovedDefinitionHandler(object):
    def __init__(self, real_module, moved_definitions):
        self.real_module = real_module
        self.moved_definitions = moved_definitions

    def __getattr__(self, name):
        try:
            return getattr(self.real_module, name)
        except AttributeError as e:
            try:
                # is the missing name one of our moved definitions?
                new_module_name = self.moved_definitions[name]
            except KeyError:
                # raise the original AttributeError without including the inner try/catch
                # in the stack trace
                raise e from None

            warnings.warn(
                "%s has been moved from wagtail.admin.forms to %s" % (name, new_module_name),
                category=RemovedInWagtail25Warning
            )

            # load the requested definition from the module named in moved_definitions
            new_module = import_module(new_module_name)
            definition = getattr(new_module, name)

            # stash that definition into the current module so that we don't have to
            # redo this import next time we access it
            setattr(self.real_module, name, definition)

            return definition


sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS)
