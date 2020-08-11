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
        help_text="<em>please</em> be polite"
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


def make_types_test_form_page(**kwargs):
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
        label="Single line text",
        field_type='singleline',
        required=False,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=2,
        label="Multiline",
        field_type='multiline',
        required=False,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=3,
        label="Email",
        field_type='email',
        required=False,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=4,
        label="Number",
        field_type='number',
        required=False,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=5,
        label="URL",
        field_type='url',
        required=False,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=6,
        label="Checkbox",
        field_type='checkbox',
        required=False,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=7,
        label="Checkboxes",
        field_type='checkboxes',
        required=False,
        choices='foo,bar,baz',
    )
    FormField.objects.create(
        page=form_page,
        sort_order=8,
        label="Drop down",
        field_type='dropdown',
        required=False,
        choices='spam,ham,eggs',
    )
    FormField.objects.create(
        page=form_page,
        sort_order=9,
        label="Multiple select",
        field_type='multiselect',
        required=False,
        choices='qux,quux,quuz,corge',
    )
    FormField.objects.create(
        page=form_page,
        sort_order=10,
        label="Radio buttons",
        field_type='radio',
        required=False,
        choices='wibble,wobble,wubble',
    )
    FormField.objects.create(
        page=form_page,
        sort_order=11,
        label="Date",
        field_type='date',
        required=False,
    )
    FormField.objects.create(
        page=form_page,
        sort_order=12,
        label="Datetime",
        field_type='datetime',
        required=False,
    )

    return form_page
