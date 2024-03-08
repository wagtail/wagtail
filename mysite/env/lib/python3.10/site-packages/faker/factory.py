import locale as pylocale
import logging
import sys

from importlib import import_module
from typing import Any, List, Optional, Tuple

from .config import AVAILABLE_LOCALES, DEFAULT_LOCALE, PROVIDERS
from .generator import Generator
from .utils.loading import list_module

logger = logging.getLogger(__name__)

# identify if python is being run in interactive mode. If so, disable logging.
inREPL = bool(getattr(sys, "ps1", False))
if inREPL:
    logger.setLevel(logging.CRITICAL)
else:
    logger.debug("Not in REPL -> leaving logger event level as is.")


class Factory:
    @classmethod
    def create(
        cls,
        locale: Optional[str] = None,
        providers: Optional[List[str]] = None,
        generator: Optional[Generator] = None,
        includes: Optional[List[str]] = None,
        # Should we use weightings (more realistic) or weight every element equally (faster)?
        # By default, use weightings for backwards compatibility & realism
        use_weighting: bool = True,
        **config: Any,
    ) -> Generator:
        if includes is None:
            includes = []

        # fix locale to package name
        locale = locale.replace("-", "_") if locale else DEFAULT_LOCALE
        locale = pylocale.normalize(locale).split(".")[0]
        if locale not in AVAILABLE_LOCALES:
            msg = f"Invalid configuration for faker locale `{locale}`"
            raise AttributeError(msg)

        config["locale"] = locale
        config["use_weighting"] = use_weighting
        providers = providers or PROVIDERS

        providers += includes

        faker = generator or Generator(**config)

        for prov_name in providers:
            if prov_name == "faker.providers":
                continue

            prov_cls, lang_found, _ = cls._find_provider_class(prov_name, locale)
            provider = prov_cls(faker)
            provider.__use_weighting__ = use_weighting
            provider.__provider__ = prov_name
            provider.__lang__ = lang_found
            faker.add_provider(provider)

        return faker

    @classmethod
    def _find_provider_class(
        cls,
        provider_path: str,
        locale: Optional[str] = None,
    ) -> Tuple[Any, Optional[str], Optional[str]]:
        provider_module = import_module(provider_path)
        default_locale = getattr(provider_module, "default_locale", "")

        if getattr(provider_module, "localized", False):
            logger.debug(
                "Looking for locale `%s` in provider `%s`.",
                locale,
                provider_module.__name__,
            )

            available_locales = list_module(provider_module)
            if not locale or locale not in available_locales:
                unavailable_locale = locale
                locale = default_locale or DEFAULT_LOCALE
                logger.debug(
                    "Specified locale `%s` is not available for "
                    "provider `%s`. Locale reset to `%s` for this "
                    "provider.",
                    unavailable_locale,
                    provider_module.__name__,
                    locale,
                )
            else:
                logger.debug(
                    "Provider `%s` has been localized to `%s`.",
                    provider_module.__name__,
                    locale,
                )

            path = f"{provider_path}.{locale}"
            provider_module = import_module(path)

        else:
            if locale:
                logger.debug(
                    "Provider `%s` does not feature localization. "
                    "Specified locale `%s` is not utilized for this "
                    "provider.",
                    provider_module.__name__,
                    locale,
                )
            locale = default_locale = None

        return provider_module.Provider, locale, default_locale  # type: ignore
