from django import forms
from django.forms.models import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from wagtail.admin.widgets import AdminPageChooser
from wagtail.contrib.search_promotions.models import Query, SearchPromotion


class QueryForm(forms.ModelForm):
    query_string = forms.CharField(
        label=_("Search term(s)/phrase"),
        help_text=_(
            "Enter the full search string to match. An "
            "exact match is required for your Promoted Results to be "
            "displayed, wildcards are NOT allowed."
        ),
        required=True,
    )

    def clean(self):
        # We allow using an existing query string on the CreateView, so we need
        # to skip the unique validation on `query_string`. This can be done by
        # overriding the `clean()` method without calling `super().clean()`:
        # https://docs.djangoproject.com/en/stable/topics/forms/modelforms/#overriding-the-clean-method
        pass

    class Meta:
        model = Query
        fields = ["query_string"]


class SearchPromotionForm(forms.ModelForm):
    sort_order = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["page"].widget = AdminPageChooser()

    def clean(self):
        cleaned_data = super().clean()

        # Use the raw value instead of from form.cleaned_data so we don't
        # consider an invalid field as empty. For example, leaving the
        # page field empty and entering an invalid external_link_url
        # shouldn't raise an error about needing to enter a page or URL,
        # since the user *has* entered (or tried to enter) a URL.
        page = self["page"].value()
        external_link_url = self["external_link_url"].value()
        external_link_text = self["external_link_text"].value()

        # Must supply a page or external_link_url (but not both)
        if page is None:
            if external_link_url:
                # if an external_link_url is supplied,
                # then external_link_text is also required
                if not external_link_text:
                    self.add_error(
                        "external_link_text",
                        forms.ValidationError(
                            _(
                                "You must enter an external link text if you enter an external link URL."
                            )
                        ),
                    )
            else:
                self.add_error(
                    None,
                    forms.ValidationError(
                        _("You must recommend a page OR an external link.")
                    ),
                )
        elif external_link_url:
            self.add_error(
                None,
                forms.ValidationError(
                    _("Please only select a page OR enter an external link.")
                ),
            )

        return cleaned_data

    class Meta:
        model = SearchPromotion
        fields = (
            "query",
            "page",
            "external_link_url",
            "external_link_text",
            "description",
        )

        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


SearchPromotionsFormSetBase = inlineformset_factory(
    Query,
    SearchPromotion,
    form=SearchPromotionForm,
    can_order=True,
    can_delete=True,
    extra=0,
)


class SearchPromotionsFormSet(SearchPromotionsFormSetBase):
    minimum_forms = 1
    minimum_forms_message = _(
        "Please specify at least one recommendation for this search term."
    )

    def add_fields(self, form, *args, **kwargs):
        super().add_fields(form, *args, **kwargs)

        # Hide delete and order fields
        form.fields["DELETE"].widget = forms.HiddenInput()
        form.fields["ORDER"].widget = forms.HiddenInput()

        # Remove query field
        del form.fields["query"]

    def clean(self):
        # Search pick must have at least one recommended page to be valid
        # Check there is at least one non-deleted form.
        non_deleted_forms = self.total_form_count()
        non_empty_forms = 0
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            if self.can_delete and self._should_delete_form(form):
                non_deleted_forms -= 1
            if not (form.instance.id is None and not form.has_changed()):
                non_empty_forms += 1
        if (
            non_deleted_forms < self.minimum_forms
            or non_empty_forms < self.minimum_forms
        ):
            raise forms.ValidationError(self.minimum_forms_message)
