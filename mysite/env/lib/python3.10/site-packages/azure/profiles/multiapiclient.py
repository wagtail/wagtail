#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
from . import KnownProfiles, ProfileDefinition

class InvalidMultiApiClientError(Exception):
    """If the mixin is not used with a compatible class.
    """
    pass

class MultiApiClientMixin(object):
    """Mixin that contains multi-api version profile management.

    To use this mixin, a client must define two class attributes:
    - LATEST_PROFILE : a ProfileDefinition correspond to latest profile
    - _PROFILE_TAG : a tag that filter a full profile for this particular client

    This should not be used directly and will only provide private methods.
    """

    def __init__(self, *args, **kwargs):
        # Consume "api_version" and "profile", to avoid sending them to base class
        api_version = kwargs.pop("api_version", None)
        profile = kwargs.pop("profile", KnownProfiles.default)

        # Can't do "super" call here all the time, or I would break old client with:
        # TypeError: object.__init__() takes no parameters
        # So I try to detect if I correctly use this class as a Mixin, or the messed-up
        # approach like before. If I think it's the messed-up old approach,
        # don't call super
        if args or "creds" in kwargs or "config" in kwargs:
            super(MultiApiClientMixin, self).__init__(*args, **kwargs)

        try:
            type(self).LATEST_PROFILE
        except AttributeError:
            raise InvalidMultiApiClientError("To use this mixin, main client MUST define LATEST_PROFILE class attribute")

        try:
            type(self)._PROFILE_TAG
        except AttributeError:
            raise InvalidMultiApiClientError("To use this mixin, main client MUST define _PROFILE_TAG class attribute")

        if api_version and profile is not KnownProfiles.default:
            raise ValueError("Cannot use api-version and profile parameters at the same time")

        if api_version:
            self.profile = ProfileDefinition({
                self._PROFILE_TAG: {
                    None: api_version
                }},
                self._PROFILE_TAG + " " + api_version
            )
        elif isinstance(profile, dict):
            self.profile = ProfileDefinition({
                self._PROFILE_TAG: profile,
                },
                self._PROFILE_TAG + " dict"
            )
            if api_version:
                self.profile._profile_dict[self._PROFILE_TAG][None] = api_version
        else:
            self.profile = profile

    def _get_api_version(self, operation_group_name):
        current_profile = self.profile
        if self.profile is KnownProfiles.default:
            current_profile = KnownProfiles.default.value.definition()

        if current_profile is KnownProfiles.latest:
            current_profile = self.LATEST_PROFILE
        elif isinstance(current_profile, KnownProfiles):
            current_profile = current_profile.value
        elif isinstance(current_profile, ProfileDefinition):
            pass  # I expect that
        else:
            raise ValueError("Cannot determine a ProfileDefinition from {}".format(self.profile))

        local_profile_dict = current_profile.get_profile_dict()
        if self._PROFILE_TAG not in local_profile_dict:
            raise ValueError("This profile doesn't define {}".format(self._PROFILE_TAG))

        local_profile = local_profile_dict[self._PROFILE_TAG]
        if operation_group_name in local_profile:
            return local_profile[operation_group_name]
        try:
            return local_profile[None]
        except KeyError:
            raise ValueError("This profile definition does not contain a default API version")
