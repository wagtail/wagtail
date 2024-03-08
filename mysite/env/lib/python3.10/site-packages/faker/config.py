from importlib import import_module

from .utils.loading import find_available_locales, find_available_providers

DEFAULT_LOCALE = "en_US"

META_PROVIDERS_MODULES = [
    "faker.providers",
]

PROVIDERS = find_available_providers([import_module(path) for path in META_PROVIDERS_MODULES])

AVAILABLE_LOCALES = find_available_locales(PROVIDERS)
