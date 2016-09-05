# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from wagtail.tests.testapp.models import FormField, FormPage
from wagtail.wagtailcore.models import Page


def make_form_page(**kwargs):
    kwargs.setdefault('title', "Contact us")
    kwargs.setdefault('slug', "contact-us")
    kwargs.setdefault('to_address', "to@email.com")
    kwargs.setdefault('from_address', "from@email.com")
    kwargs.setdefault('subject', "The subject")

    home_page = Page.objects.get(url_path='/home/')
    form_page = home_page.add_child(instance=FormPage(**kwargs))

    FormField.objects.create(
        page=form_page,
        sort_order=1,
        label="Your email",
        field_type='email',
        required=True,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=2,
        label="Your message",
        field_type='multiline',
        required=True,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=3,
        label="Your choices",
        field_type='checkboxes',
        required=False,
        choices='foo,bar,baz',
    )

    return form_page

# TODO: add make_form_page_with_custom_submission
