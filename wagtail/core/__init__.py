def load_tests(loader, tests, pattern):
    # As standard the unittest framework will recurse through this module, importing submodules to
    # discover tests. We don't want it to do that for wagtail.core, because it will trigger our
    # deprecation warnings. This standard behaviour can be overridden by defining a load_tests
    # function that returns a TestSuite to run; return None so that no tests are run and no
    # recursive importing happens.
    return None
