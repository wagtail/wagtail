#-------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
#--------------------------------------------------------------------------
try:
    from msrest.exceptions import (
        ClientException,
        SerializationError,
        DeserializationError,
        TokenExpiredError,
        ClientRequestError,
        AuthenticationError,
        HttpOperationError,
    )
except ImportError:
    raise ImportError("You need to install 'msrest' to use this feature")

try:
    from msrestazure.azure_exceptions import CloudError
except ImportError:
    raise ImportError("You need to install 'msrestazure' to use this feature")
