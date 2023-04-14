import itertools
import os
import re
from collections import defaultdict

from django import forms
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _

from wagtail import hooks
from wagtail.admin import messages
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.rich_text import get_rich_text_editor_widget
from wagtail.admin.widgets import (
    AdminAutoHeightTextInput,
    AdminDateInput,
    AdminDateTimeInput,
    AdminPageChooser,
    AdminTimeInput,
    SwitchInput,
)
from wagtail.documents.widgets import AdminDocumentChooser
from wagtail.images.widgets import AdminImageChooser
from wagtail.models import Page
from wagtail.snippets.widgets import AdminSnippetChooser


class FakeAdminSnippetChooser(AdminSnippetChooser):
    """
    AdminSnippetChooser can't be used on non-snippet models (because it fails when constructing the
    URL to the chooser modal), and we can't guarantee that any given Wagtail installation using
    this style guide will have any snippet models registered. We therefore override the
    get_chooser_modal_url method so that we can use it with Page as a stand-in for a real snippet.
    """

    def get_chooser_modal_url(self):
        return "/"


class ExampleForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["page_chooser"].widget = AdminPageChooser()
        self.fields["image_chooser"].widget = AdminImageChooser()
        self.fields["document_chooser"].widget = AdminDocumentChooser()
        self.fields["snippet_chooser"].widget = FakeAdminSnippetChooser(Page)
        self.fields["date"].widget = AdminDateInput()
        self.fields["time"].widget = AdminTimeInput()
        self.fields["datetime"].widget = AdminDateTimeInput()
        self.fields["auto_height_text"].widget = AdminAutoHeightTextInput()
        self.fields["default_rich_text"].widget = get_rich_text_editor_widget("default")
        self.fields["switch"].widget = SwitchInput()
        self.fields["disabled_switch"].widget = SwitchInput(attrs={"disabled": True})

    CHOICES = (
        ("choice1", "choice 1"),
        ("choice2", "choice 2 that is longer but pretty normal"),
        (
            "choice3",
            """
            choice 3 that has a very long label that it cannot possibly fit within the
            width of the parent container but we're going to test it anyway to see
            what happens and how it wraps and whether it breaks the layout or not
            """,
        ),
    )

    text = forms.CharField(required=True, help_text="help text")
    auto_height_text = forms.CharField(required=True)
    default_rich_text = forms.CharField(required=True)
    url = forms.URLField(required=True)
    email = forms.EmailField(max_length=254)
    date = forms.DateField()
    time = forms.TimeField()
    datetime = forms.DateTimeField()
    select = forms.ChoiceField(choices=CHOICES[:2])
    long_select = forms.ChoiceField(choices=CHOICES)
    radio_select = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)
    multiple_select = forms.MultipleChoiceField(choices=CHOICES)
    multiple_checkbox = forms.MultipleChoiceField(
        choices=CHOICES, widget=forms.CheckboxSelectMultiple
    )
    boolean = forms.BooleanField(required=False)
    switch = forms.BooleanField(required=False)
    disabled_switch = forms.BooleanField(required=False)
    page_chooser = forms.BooleanField(required=True)
    image_chooser = forms.BooleanField(required=True)
    document_chooser = forms.BooleanField(required=True)
    snippet_chooser = forms.BooleanField(required=True)


icon_id_pattern = re.compile(r"id=\"icon-([a-z0-9-]+)\"")
icon_comment_pattern = re.compile(r"<!--!(.*?)-->")


def index(request):

    form = SearchForm(placeholder=_("Search something"))

    example_form = ExampleForm()

    messages.success(
        request,
        _("Success message"),
        buttons=[messages.button("", _("View live")), messages.button("", _("Edit"))],
    )
    messages.warning(
        request,
        _("Warning message"),
        buttons=[messages.button("", _("View live")), messages.button("", _("Edit"))],
    )
    messages.error(
        request,
        _("Error message"),
        buttons=[messages.button("", _("View live")), messages.button("", _("Edit"))],
    )

    paginator = Paginator(list(range(100)), 10)
    page = paginator.page(2)

    icon_hooks = hooks.get_hooks("register_icons")
    registered_icons = itertools.chain.from_iterable(hook([]) for hook in icon_hooks)
    all_icons = defaultdict(list)
    for icon_path in registered_icons:
        folder, filename = os.path.split(icon_path)
        icon = render_to_string(icon_path)
        id_match = icon_id_pattern.search(icon)
        name = id_match.group(1) if id_match else None
        source_match = icon_comment_pattern.search(icon)

        all_icons[folder].append(
            {
                "folder": folder,
                "file_path": icon_path,
                "name": name,
                "source": source_match.group(1) if source_match else None,
                "icon": icon,
            }
        )

    return TemplateResponse(
        request,
        "wagtailstyleguide/base.html",
        {
            "all_icons": all_icons.items(),
            "search_form": form,
            "example_form": example_form,
            "example_page": page,
        },
    )
