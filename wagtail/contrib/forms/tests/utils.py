# -*- coding: utf-8 -*-
from wagtail.core.models import Page
from wagtail.tests.testapp.models import (
    FormField, FormFieldWithCustomSubmission, FormPage, FormPageWithCustomSubmission,
    FormPageWithRedirect, RedirectFormField)


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


def make_form_page_with_custom_submission(**kwargs):
    kwargs.setdefault('title', "Contact us")
    kwargs.setdefault('intro', "<p>Boring intro text</p>")
    kwargs.setdefault('thank_you_text', "<p>Thank you for your patience!</p>")
    kwargs.setdefault('slug', "contact-us")
    kwargs.setdefault('to_address', "to@email.com")
    kwargs.setdefault('from_address', "from@email.com")
    kwargs.setdefault('subject', "The subject")

    home_page = Page.objects.get(url_path='/home/')
    form_page = home_page.add_child(instance=FormPageWithCustomSubmission(**kwargs))

    FormFieldWithCustomSubmission.objects.create(
        page=form_page,
        sort_order=1,
        label="Your email",
        field_type='email',
        required=True,
    )
    FormFieldWithCustomSubmission.objects.create(
        page=form_page,
        sort_order=2,
        label="Your message",
        field_type='multiline',
        required=True,
    )
    FormFieldWithCustomSubmission.objects.create(
        page=form_page,
        sort_order=3,
        label="Your choices",
        field_type='checkboxes',
        required=False,
        choices='foo,bar,baz',
    )

    return form_page


def make_form_page_with_redirect(**kwargs):
    kwargs.setdefault('title', "Contact us")
    kwargs.setdefault('slug', "contact-us")
    kwargs.setdefault('to_address', "to@email.com")
    kwargs.setdefault('from_address', "from@email.com")
    kwargs.setdefault('subject', "The subject")


    home_page = Page.objects.get(url_path='/home/')
    kwargs.setdefault('thank_you_redirect_page', home_page)
    form_page = home_page.add_child(instance=FormPageWithRedirect(**kwargs))
    # form_page.thank_you_redirect_page = home_page

    RedirectFormField.objects.create(
        page=form_page,
        sort_order=1,
        label="Your email",
        field_type='email',
        required=True,
    )
    RedirectFormField.objects.create(
        page=form_page,
        sort_order=2,
        label="Your message",
        field_type='multiline',
        required=True,
    )
    RedirectFormField.objects.create(
        page=form_page,
        sort_order=3,
        label="Your choices",
        field_type='checkboxes',
        required=False,
        choices='foo,bar,baz',
    )

    return form_page
