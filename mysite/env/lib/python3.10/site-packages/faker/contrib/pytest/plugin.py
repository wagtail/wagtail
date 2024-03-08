import pytest

from faker import Faker
from faker.config import DEFAULT_LOCALE

DEFAULT_SEED = 0


@pytest.fixture(scope="session", autouse=True)
def _session_faker(request):
    """Fixture that stores the session level ``Faker`` instance.

    This fixture is internal and is only meant for use within the project.
    Third parties should instead use the ``faker`` fixture for their tests.
    """
    if "faker_session_locale" in request.fixturenames:
        locale = request.getfixturevalue("faker_session_locale")
    else:
        locale = [DEFAULT_LOCALE]
    return Faker(locale=locale)


@pytest.fixture()
def faker(request):
    """Fixture that returns a seeded and suitable ``Faker`` instance."""
    if "faker_locale" in request.fixturenames:
        locale = request.getfixturevalue("faker_locale")
        fake = Faker(locale=locale)
    else:
        fake = request.getfixturevalue("_session_faker")

    seed = DEFAULT_SEED
    if "faker_seed" in request.fixturenames:
        seed = request.getfixturevalue("faker_seed")
    fake.seed_instance(seed=seed)
    fake.unique.clear()

    return fake
