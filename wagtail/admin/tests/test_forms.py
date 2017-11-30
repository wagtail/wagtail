from django.forms.fields import CharField
from django.test import TestCase

from wagtail.admin.forms import LoginForm


class CustomLoginForm(LoginForm):
    captcha = CharField(
        label='Captcha', help_text="should be in extra_fields()")


class TestLoginForm(TestCase):

    def test_extra_fields(self):
        form = CustomLoginForm()
        self.assertEqual(list(form.extra_fields), [
            ('captcha', form.fields['captcha'])
        ])
