#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------

def get_cli_active_cloud():
    """Return a CLI active cloud.

    *Disclaimer*: This method is not working for azure-cli-core>=2.21.0 (released in March 2021).

    .. versionadded:: 1.1.6

    .. deprecated:: 1.1.28

    :return: A CLI Cloud
    :rtype: azure.cli.core.cloud.Cloud
    :raises: ImportError if azure-cli-core package is not available
    """

    try:
        from azure.cli.core.cloud import get_active_cloud
    except ImportError:
        raise ImportError(
            "The public API of azure-cli-core has been deprecated starting 2.21.0, " +
            "and this method no longer can return a cloud instance. " +
            "If you want to use this method, you need to install 'azure-cli-core<2.21.0'. " +
            "You may corrupt data if you use current CLI and old azure-cli-core."
        )
    return get_active_cloud()
