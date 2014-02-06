import re


def camelcase_to_underscore(str):
    # http://djangosnippets.org/snippets/585/
    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')
