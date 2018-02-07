import sys
import warnings
from contextlib import contextmanager

from django.contrib.auth import get_user_model
from django.test.testcases import assert_and_parse_html

from .assert_logs import _AssertLogsContext


class WagtailTestUtils:

    @staticmethod
    def create_test_user():
        """
        Override this method to return an instance of your custom user model
        """
        user_model = get_user_model()
        # Create a user
        user_data = dict()
        user_data[user_model.USERNAME_FIELD] = 'test@email.com'
        user_data['password'] = 'password'

        for field in user_model.REQUIRED_FIELDS:
            user_data[field] = field

        return user_model.objects.create_superuser(**user_data)

    def login(self):
        user = self.create_test_user()

        user_model = get_user_model()
        # Login
        self.assertTrue(
            self.client.login(password='password', **{user_model.USERNAME_FIELD: 'test@email.com'})
        )

        return user

    @staticmethod
    @contextmanager
    def ignore_deprecation_warnings():
        with warnings.catch_warnings(record=True) as warning_list:  # catch all warnings
            yield

        # rethrow all warnings that were not DeprecationWarnings or PendingDeprecationWarnings
        for w in warning_list:
            if not issubclass(w.category, (DeprecationWarning, PendingDeprecationWarning)):
                warnings.showwarning(
                    message=w.message,
                    category=w.category,
                    filename=w.filename,
                    lineno=w.lineno,
                    file=w.file,
                    line=w.line
                )

    # borrowed from https://github.com/django/django/commit/9f427617e4559012e1c2fd8fce46cbe225d8515d
    @staticmethod
    def reset_warning_registry():
        """
        Clear warning registry for all modules. This is required in some tests
        because of a bug in Python that prevents warnings.simplefilter("always")
        from always making warnings appear: http://bugs.python.org/issue4180

        The bug was fixed in Python 3.4.2.
        """
        key = "__warningregistry__"
        for mod in list(sys.modules.values()):
            if hasattr(mod, key):
                getattr(mod, key).clear()

    # Configuring LOGGING_FORMAT is not possible without subclassing
    # unittest.TestCase, so use this implementation even on Python 3.4
    def assertLogs(self, logger=None, level=None):
        """Fail unless a log message of level *level* or higher is emitted
        on *logger_name* or its children.  If omitted, *level* defaults to
        INFO and *logger* defaults to the root logger.

        This method must be used as a context manager, and will yield
        a recording object with two attributes: `output` and `records`.
        At the end of the context manager, the `output` attribute will
        be a list of the matching formatted log messages and the
        `records` attribute will be a list of the corresponding LogRecord
        objects.

        Example::

            with self.assertLogs('foo', level='INFO') as cm:
                logging.getLogger('foo').info('first message')
                logging.getLogger('foo.bar').error('second message')
            self.assertEqual(cm.output, ['INFO:foo:first message',
                                         'ERROR:foo.bar:second message'])
        """
        return _AssertLogsContext(self, logger, level)

    @contextmanager
    def register_hook(self, hook_name, fn, order=0):
        from wagtail.core import hooks

        hooks.register(hook_name, fn, order)
        try:
            yield
        finally:
            hooks._hooks[hook_name].remove((fn, order))

    def _tag_is_equal(self, tag1, tag2):
        if not hasattr(tag1, 'name') or not hasattr(tag2, 'name'):
            return False
        if tag1.name != tag2.name:
            return False
        if len(tag1.attributes) != len(tag2.attributes):
            return False
        if tag1.attributes != tag2.attributes:
            # attributes without a value is same as attribute with value that
            # equals the attributes name:
            # <input checked> == <input checked="checked">
            for i in range(len(tag1.attributes)):
                attr, value = tag1.attributes[i]
                other_attr, other_value = tag2.attributes[i]
                if value is None:
                    value = attr
                if other_value is None:
                    other_value = other_attr
                if attr != other_attr or value != other_value:
                    return False
        return True

    def _tag_matches_with_extra_attrs(self, thin_tag, fat_tag):
        # return true if thin_tag and fat_tag have the same name,
        # and all attributes on thin_tag exist on fat_tag
        if not hasattr(thin_tag, 'name') or not hasattr(fat_tag, 'name'):
            return False
        if thin_tag.name != fat_tag.name:
            return False
        for attr, value in thin_tag.attributes:
            if value is None:
                # attributes without a value is same as attribute with value that
                # equals the attributes name:
                # <input checked> == <input checked="checked">
                if (attr, None) not in fat_tag.attributes and (attr, attr) not in fat_tag.attributes:
                    return False
            else:
                if (attr, value) not in fat_tag.attributes:
                    return False

        return True

    def _count_tag_occurrences(self, needle, haystack, allow_extra_attrs=False):
        count = 0

        if allow_extra_attrs:
            if self._tag_matches_with_extra_attrs(needle, haystack):
                count += 1
        else:
            if self._tag_is_equal(needle, haystack):
                count += 1

        if hasattr(haystack, 'children'):
            count += sum(
                self._count_tag_occurrences(needle, child, allow_extra_attrs=allow_extra_attrs)
                for child in haystack.children
            )

        return count

    def _tag_is_template_script(self, tag):
        if tag.name != 'script':
            return False
        return any(attr == ('type', 'text/template') for attr in tag.attributes)

    def _find_template_script_tags(self, haystack):
        if not hasattr(haystack, 'name'):
            return

        if self._tag_is_template_script(haystack):
            yield haystack
        else:
            for child in haystack.children:
                for script_tag in self._find_template_script_tags(child):
                    yield script_tag

    def assertTagInHTML(self, needle, haystack, count=None, msg_prefix='', allow_extra_attrs=False):
        needle = assert_and_parse_html(self, needle, None, 'First argument is not valid HTML:')
        haystack = assert_and_parse_html(self, haystack, None, 'Second argument is not valid HTML:')
        real_count = self._count_tag_occurrences(needle, haystack, allow_extra_attrs=allow_extra_attrs)
        if count is not None:
            self.assertEqual(
                real_count, count,
                msg_prefix + "Found %d instances of '%s' in response (expected %d)" % (real_count, needle, count)
            )
        else:
            self.assertTrue(real_count != 0, msg_prefix + "Couldn't find '%s' in response" % needle)

    def assertNotInHTML(self, needle, haystack, msg_prefix=''):
        self.assertInHTML(needle, haystack, count=0, msg_prefix=msg_prefix)

    def assertTagInTemplateScript(self, needle, haystack, count=None, msg_prefix=''):
        needle = assert_and_parse_html(self, needle, None, 'First argument is not valid HTML:')
        haystack = assert_and_parse_html(self, haystack, None, 'Second argument is not valid HTML:')
        real_count = 0

        for script_tag in self._find_template_script_tags(haystack):
            if script_tag.children:
                self.assertEqual(len(script_tag.children), 1)
                script_html = assert_and_parse_html(
                    self, script_tag.children[0], None, 'Script tag content is not valid HTML:'
                )
                real_count += self._count_tag_occurrences(needle, script_html)

        if count is not None:
            self.assertEqual(
                real_count, count,
                msg_prefix + "Found %d instances of '%s' in template script (expected %d)" % (real_count, needle, count)
            )
        else:
            self.assertTrue(real_count != 0, msg_prefix + "Couldn't find '%s' in template script" % needle)
