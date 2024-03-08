from __future__ import annotations

import copy
import functools
import re

from collections import OrderedDict
from random import Random
from typing import Any, Callable, Dict, List, Optional, Pattern, Sequence, Tuple, TypeVar, Union

from .config import DEFAULT_LOCALE
from .exceptions import UniquenessException
from .factory import Factory
from .generator import Generator, random
from .typing import SeedType
from .utils.distribution import choices_distribution

_UNIQUE_ATTEMPTS = 1000

RetType = TypeVar("RetType")


class Faker:
    """Proxy class capable of supporting multiple locales"""

    cache_pattern: Pattern = re.compile(r"^_cached_\w*_mapping$")
    generator_attrs = [
        attr for attr in dir(Generator) if not attr.startswith("__") and attr not in ["seed", "seed_instance", "random"]
    ]

    def __init__(
        self,
        locale: Optional[Union[str, Sequence[str], Dict[str, Union[int, float]]]] = None,
        providers: Optional[List[str]] = None,
        generator: Optional[Generator] = None,
        includes: Optional[List[str]] = None,
        use_weighting: bool = True,
        **config: Any,
    ) -> None:
        self._factory_map: OrderedDict[str, Generator | Faker] = OrderedDict()
        self._weights = None
        self._unique_proxy = UniqueProxy(self)
        self._optional_proxy = OptionalProxy(self)

        if isinstance(locale, str):
            locales = [locale.replace("-", "_")]

        # This guarantees a FIFO ordering of elements in `locales` based on the final
        # locale string while discarding duplicates after processing
        elif isinstance(locale, (list, tuple, set)):
            locales = []
            for code in locale:
                if not isinstance(code, str):
                    raise TypeError(f'The locale "{str(code)}" must be a string.')
                final_locale = code.replace("-", "_")
                if final_locale not in locales:
                    locales.append(final_locale)

        elif isinstance(locale, (OrderedDict, dict)):
            assert all(isinstance(v, (int, float)) for v in locale.values())
            odict = OrderedDict()
            for k, v in locale.items():
                key = k.replace("-", "_")
                odict[key] = v
            locales = list(odict.keys())
            self._weights = list(odict.values())

        else:
            locales = [DEFAULT_LOCALE]

        if len(locales) == 1:
            self._factory_map[locales[0]] = Factory.create(
                locales[0],
                providers,
                generator,
                includes,
                use_weighting=use_weighting,
                **config,
            )
        else:
            for locale in locales:
                self._factory_map[locale] = Faker(
                    locale,
                    providers,
                    generator,
                    includes,
                    use_weighting=use_weighting,
                    **config,
                )

        self._locales = locales
        self._factories = list(self._factory_map.values())

    def __dir__(self):
        attributes = set(super(Faker, self).__dir__())
        for factory in self.factories:
            attributes |= {attr for attr in dir(factory) if not attr.startswith("_")}
        return sorted(attributes)

    def __getitem__(self, locale: str) -> Faker:
        if locale.replace("-", "_") in self.locales and len(self.locales) == 1:
            return self
        instance = self._factory_map[locale.replace("-", "_")]
        assert isinstance(instance, Faker)  # for mypy
        return instance

    def __getattribute__(self, attr: str) -> Any:
        """
        Handles the "attribute resolution" behavior for declared members of this proxy class

        The class method `seed` cannot be called from an instance.

        :param attr: attribute name
        :return: the appropriate attribute
        """
        if attr == "seed":
            msg = "Calling `.seed()` on instances is deprecated. " "Use the class method `Faker.seed()` instead."
            raise TypeError(msg)
        else:
            return super().__getattribute__(attr)

    def __getattr__(self, attr: str) -> Any:
        """
        Handles cache access and proxying behavior

        :param attr: attribute name
        :return: the appropriate attribute
        """
        if len(self._factories) == 1:
            return getattr(self._factories[0], attr)
        elif attr in self.generator_attrs:
            msg = "Proxying calls to `%s` is not implemented in multiple locale mode." % attr
            raise NotImplementedError(msg)
        elif self.cache_pattern.match(attr):
            msg = "Cached attribute `%s` does not exist" % attr
            raise AttributeError(msg)
        else:
            factory = self._select_factory(attr)
            return getattr(factory, attr)

    def __deepcopy__(self, memodict: Dict = {}) -> "Faker":
        cls = self.__class__
        result = cls.__new__(cls)
        result._locales = copy.deepcopy(self._locales)
        result._factories = copy.deepcopy(self._factories)
        result._factory_map = copy.deepcopy(self._factory_map)
        result._weights = copy.deepcopy(self._weights)
        result._unique_proxy = UniqueProxy(self)
        result._unique_proxy._seen = {k: {result._unique_proxy._sentinel} for k in self._unique_proxy._seen.keys()}
        return result

    def __setstate__(self, state: Any) -> None:
        self.__dict__.update(state)

    @property
    def unique(self) -> "UniqueProxy":
        return self._unique_proxy

    @property
    def optional(self) -> "OptionalProxy":
        return self._optional_proxy

    def _select_factory(self, method_name: str) -> Factory:
        """
        Returns a random factory that supports the provider method

        :param method_name: Name of provider method
        :return: A factory that supports the provider method
        """

        factories, weights = self._map_provider_method(method_name)

        if len(factories) == 0:
            msg = f"No generator object has attribute {method_name!r}"
            raise AttributeError(msg)
        elif len(factories) == 1:
            return factories[0]

        if weights:
            factory = self._select_factory_distribution(factories, weights)
        else:
            factory = self._select_factory_choice(factories)
        return factory

    def _select_factory_distribution(self, factories, weights):
        return choices_distribution(factories, weights, random, length=1)[0]

    def _select_factory_choice(self, factories):
        return random.choice(factories)

    def _map_provider_method(self, method_name: str) -> Tuple[List[Factory], Optional[List[float]]]:
        """
        Creates a 2-tuple of factories and weights for the given provider method name

        The first element of the tuple contains a list of compatible factories.
        The second element of the tuple contains a list of distribution weights.

        :param method_name: Name of provider method
        :return: 2-tuple (factories, weights)
        """

        # Return cached mapping if it exists for given method
        attr = f"_cached_{method_name}_mapping"
        if hasattr(self, attr):
            return getattr(self, attr)

        # Create mapping if it does not exist
        if self._weights:
            value = [
                (factory, weight)
                for factory, weight in zip(self.factories, self._weights)
                if hasattr(factory, method_name)
            ]
            factories, weights = zip(*value)
            mapping = list(factories), list(weights)
        else:
            value = [factory for factory in self.factories if hasattr(factory, method_name)]  # type: ignore
            mapping = value, None  # type: ignore

        # Then cache and return results
        setattr(self, attr, mapping)
        return mapping

    @classmethod
    def seed(cls, seed: Optional[SeedType] = None) -> None:
        """
        Hashables the shared `random.Random` object across all factories

        :param seed: seed value
        """
        Generator.seed(seed)

    def seed_instance(self, seed: Optional[SeedType] = None) -> None:
        """
        Creates and seeds a new `random.Random` object for each factory

        :param seed: seed value
        """
        for factory in self._factories:
            factory.seed_instance(seed)

    def seed_locale(self, locale: str, seed: Optional[SeedType] = None) -> None:
        """
        Creates and seeds a new `random.Random` object for the factory of the specified locale

        :param locale: locale string
        :param seed: seed value
        """
        self._factory_map[locale.replace("-", "_")].seed_instance(seed)

    @property
    def random(self) -> Random:
        """
        Proxies `random` getter calls

        In single locale mode, this will be proxied to the `random` getter
        of the only internal `Generator` object. Subclasses will have to
        implement desired behavior in multiple locale mode.
        """

        if len(self._factories) == 1:
            return self._factories[0].random
        else:
            msg = "Proxying `random` getter calls is not implemented in multiple locale mode."
            raise NotImplementedError(msg)

    @random.setter
    def random(self, value: Random) -> None:
        """
        Proxies `random` setter calls

        In single locale mode, this will be proxied to the `random` setter
        of the only internal `Generator` object. Subclasses will have to
        implement desired behavior in multiple locale mode.
        """

        if len(self._factories) == 1:
            self._factories[0].random = value
        else:
            msg = "Proxying `random` setter calls is not implemented in multiple locale mode."
            raise NotImplementedError(msg)

    @property
    def locales(self) -> List[str]:
        return list(self._locales)

    @property
    def weights(self) -> Optional[List[Union[int, float]]]:
        return self._weights

    @property
    def factories(self) -> List[Generator | Faker]:
        return self._factories

    def items(self) -> List[Tuple[str, Generator | Faker]]:
        return list(self._factory_map.items())


class UniqueProxy:
    def __init__(self, proxy: Faker):
        self._proxy = proxy
        self._seen: Dict = {}
        self._sentinel = object()

    def clear(self) -> None:
        self._seen = {}

    def __getattr__(self, name: str) -> Any:
        obj = getattr(self._proxy, name)
        if callable(obj):
            return self._wrap(name, obj)
        else:
            raise TypeError("Accessing non-functions through .unique is not supported.")

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def _wrap(self, name: str, function: Callable) -> Callable:
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            key = (name, args, tuple(sorted(kwargs.items())))

            generated = self._seen.setdefault(key, {self._sentinel})

            # With use of a sentinel value rather than None, we leave
            # None open as a valid return value.
            retval = self._sentinel

            for i in range(_UNIQUE_ATTEMPTS):
                if retval not in generated:
                    break
                retval = function(*args, **kwargs)
            else:
                raise UniquenessException(f"Got duplicated values after {_UNIQUE_ATTEMPTS:,} iterations.")

            generated.add(retval)

            return retval

        return wrapper


class OptionalProxy:
    """
    Return either a fake value or None, with a customizable probability.
    """

    def __init__(self, proxy: Faker):
        self._proxy = proxy

    def __getattr__(self, name: str) -> Any:
        obj = getattr(self._proxy, name)
        if callable(obj):
            return self._wrap(name, obj)
        else:
            raise TypeError("Accessing non-functions through .optional is not supported.")

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def _wrap(self, name: str, function: Callable[..., RetType]) -> Callable[..., Optional[RetType]]:
        @functools.wraps(function)
        def wrapper(*args: Any, prob: float = 0.5, **kwargs: Any) -> Optional[RetType]:
            if not 0 < prob <= 1.0:
                raise ValueError("prob must be between 0 and 1")
            return function(*args, **kwargs) if self._proxy.boolean(chance_of_getting_true=int(prob * 100)) else None

        return wrapper
