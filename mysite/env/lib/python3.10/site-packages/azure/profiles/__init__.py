#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
from enum import Enum

class ProfileDefinition(object):
    """Allow to define a custom Profile definition.

    Note::

    The dict format taken as input is yet to be confirmed and should
    *not* be considered as stable in the current implementation.

    :param dict profile_dict: A profile dictionnary
    :param str label: A label for pretty printing
    """
    def __init__(self, profile_dict, label=None):
        self._profile_dict = profile_dict
        self._label = label

    @property
    def label(self):
        """The label associated to this profile definition.
        """
        return self._label

    def __repr__(self):
        return self._label if self._label else self._profile_dict.__repr__()

    def get_profile_dict(self):
        """Return the current profile dict.

        This is internal information, and content should not be considered stable.
        """
        return self._profile_dict


class DefaultProfile(object):
    """Store a default profile.

    :var ProfileDefinition profile: The default profile as class attribute
    """
    profile = None

    def use(self, profile):
        """Define a new default profile."""
        if not isinstance(profile, (KnownProfiles, ProfileDefinition)):
            raise ValueError("Can only set as default a ProfileDefinition or a KnownProfiles")
        type(self).profile = profile

    def definition(self):
        return type(self).profile

class KnownProfiles(Enum):
    """This defines known Azure Profiles.

    There is two meta-profiles:

    - latest : will always use latest available api-version on each package
    - default : mutable, will define profile automatically for all packages

    If you change default, this changes all created packages on the fly to
    this profile. This can be used to switch a complete set of API Version
    without re-creating all clients.
    """

    # default - This is a meta-profile and point to another profile
    default = DefaultProfile()
    # latest - This is a meta-profile and does not contain definitions
    latest = ProfileDefinition(None, "latest")
    v2017_03_09_profile = ProfileDefinition(
        {
            "azure.keyvault.KeyVaultClient":{
                None: "2016-10-01"
            },
            "azure.mgmt.authorization.AuthorizationManagementClient": {
                None: "2015-07-01"
            },
            "azure.mgmt.compute.ComputeManagementClient": {
                None: "2016-03-30"
            },
            "azure.mgmt.keyvault.KeyVaultManagementClient":{
                None: "2016-10-01"
            },
            "azure.mgmt.network.NetworkManagementClient": {
                None: "2015-06-15"
            },
            "azure.mgmt.storage.StorageManagementClient": {
                None: "2016-01-01"
            },
            "azure.mgmt.resource.policy.PolicyClient": {
                None: "2015-10-01-preview"
            },
            "azure.mgmt.resource.locks.ManagementLockClient": {
                None: "2015-01-01"
            },
            "azure.mgmt.resource.links.ManagementLinkClient": {
                None: "2016-09-01"
            },
            "azure.mgmt.resource.resources.ResourceManagementClient": {
                None: "2016-02-01"
            },
            "azure.mgmt.resource.subscriptions.SubscriptionClient": {
                None: "2016-06-01"
            }
        },
        "2017-03-09-profile"
    )
    v2018_03_01_hybrid = ProfileDefinition(
        {
            "azure.keyvault.KeyVaultClient":{
                None: "2016-10-01"
            },
            "azure.mgmt.authorization.AuthorizationManagementClient": {
                None: "2015-07-01"
            },
            "azure.mgmt.compute.ComputeManagementClient": {
                None: "2017-03-30"
            },
            "azure.mgmt.keyvault.KeyVaultManagementClient":{
                None: "2016-10-01"
            },
            "azure.mgmt.network.NetworkManagementClient": {
                None: "2017-10-01"
            },
            "azure.mgmt.storage.StorageManagementClient": {
                None: "2016-01-01"
            },
            "azure.mgmt.resource.policy.PolicyClient": {
                None: "2016-12-01"
            },
            "azure.mgmt.resource.locks.ManagementLockClient": {
                None: "2016-09-01"
            },
            "azure.mgmt.resource.links.ManagementLinkClient": {
                None: "2016-09-01"
            },
            "azure.mgmt.resource.resources.ResourceManagementClient": {
                None: "2018-02-01"
            },
            "azure.mgmt.resource.subscriptions.SubscriptionClient": {
                None: "2016-06-01"
            },
            "azure.mgmt.dns.DnsManagementClient": {
                None: "2016-04-01"
            }
        },
        "2018-03-01-hybrid"
    )
    v2019_03_01_hybrid = ProfileDefinition(
        {
            "azure.keyvault.KeyVaultClient": {
                None: "2016-10-01"
            },
            "azure.mgmt.authorization.AuthorizationManagementClient": {
                None: "2015-07-01"
            },
            "azure.mgmt.compute.ComputeManagementClient": {
                None: "2017-12-01",
                'resource_skus': '2017-09-01',
                'disks': '2017-03-30',
                'snapshots': '2017-03-30'
            },
            "azure.mgmt.keyvault.KeyVaultManagementClient":{
                None: "2016-10-01"
            },
            "azure.mgmt.monitor.MonitorManagementClient": {
                'metric_definitions': '2018-01-01',
                'metrics': '2018-01-01',
                'diagnostic_settings': '2017-05-01-preview',
                'diagnostic_settings_category': '2017-05-01-preview',
                'event_categories': '2015-04-01',
                'operations': '2015-04-01',
            },
            "azure.mgmt.network.NetworkManagementClient": {
                None: "2017-10-01"
            },
            "azure.mgmt.storage.StorageManagementClient": {
                None: "2017-10-01"
            },
            "azure.mgmt.resource.policy.PolicyClient": {
                None: "2016-12-01"
            },
            "azure.mgmt.resource.locks.ManagementLockClient": {
                None: "2016-09-01"
            },
            "azure.mgmt.resource.links.ManagementLinkClient": {
                None: "2016-09-01"
            },
            "azure.mgmt.resource.resources.ResourceManagementClient": {
                None: "2018-05-01"
            },
            "azure.mgmt.resource.subscriptions.SubscriptionClient": {
                None: "2016-06-01"
            },
            "azure.mgmt.dns.DnsManagementClient": {
                None: "2016-04-01"
            }
        },
        "2019-03-01-hybrid"
    )
    v2020_09_01_hybrid = ProfileDefinition(
        {
            "azure.keyvault.KeyVaultClient": {
                None: "2016-10-01"
            },
            "azure.mgmt.authorization.AuthorizationManagementClient": {
                None: "2016-09-01"
            },
            "azure.mgmt.compute.ComputeManagementClient": {
                None: "2020-06-01",
                'resource_skus': '2019-04-01',
                'disks': '2019-07-01',
                'snapshots': '2019-07-01'
            },
            "azure.mgmt.keyvault.KeyVaultManagementClient":{
                None: "2019-09-01"
            },
            "azure.mgmt.monitor.MonitorManagementClient": {
                'metric_definitions': '2018-01-01',
                'metrics': '2018-01-01',
                'diagnostic_settings': '2017-05-01-preview',
                'diagnostic_settings_category': '2017-05-01-preview',
                'event_categories': '2015-04-01',
                'operations': '2015-04-01',
            },
            "azure.mgmt.network.NetworkManagementClient": {
                None: "2018-11-01"
            },
            "azure.mgmt.storage.StorageManagementClient": {
                None: "2019-06-01"
            },
            "azure.mgmt.resource.policy.PolicyClient": {
                None: "2016-12-01"
            },
            "azure.mgmt.resource.locks.ManagementLockClient": {
                None: "2016-09-01"
            },
            "azure.mgmt.resource.links.ManagementLinkClient": {
                None: "2016-09-01"
            },
            "azure.mgmt.resource.resources.ResourceManagementClient": {
                None: "2019-10-01"
            },
            "azure.mgmt.resource.subscriptions.SubscriptionClient": {
                None: "2016-06-01"
            },
            "azure.mgmt.dns.DnsManagementClient": {
                None: "2016-04-01"
            }
        },
        "2020-09-01-hybrid"
    )


    def __init__(self, profile_definition):
        self._profile_definition = profile_definition

    def use(self, profile):
        if self is not type(self).default:
            raise ValueError("use can only be used for `default` profile")
        self.value.use(profile)

    def definition(self):
        if self is not type(self).default:
            raise ValueError("use can only be used for `default` profile")
        return self.value.definition()

    @classmethod
    def from_name(cls, profile_name):
        if profile_name == "default":
            return cls.default
        for profile in cls:
            if isinstance(profile.value, ProfileDefinition) and profile.value.label == profile_name:
                return profile
        raise ValueError("No profile called {}".format(profile_name))


# Default profile is floating "latest"
KnownProfiles.default.use(KnownProfiles.latest)
