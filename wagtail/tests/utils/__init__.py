from wagtail.test.utils import *  # noqa

# RemovedInWagtail50Warning: We would put a deprecation warning here to tell people to import from
# wagtail.test.utils instead, but then the unittest framework would trigger the warning when
# recursing through this module during test discovery, and there seems to be no good way to block
# recursing into wagtail.test.utils without also blocking the real tests in wagtail.test.

# Instead, when wagtail/test/utils/(form_data|page_tests|wagtail_tests).py are removed in Wagtail
# 5.0, we will move this file to wagtail/test/utils.py. Since this does not match the standard
# test_*.py pattern for test modules, unittest will no longer try to import it, and then we can
# add a RemovedInWagtail60Warning to finally prompt people to update their imports.
