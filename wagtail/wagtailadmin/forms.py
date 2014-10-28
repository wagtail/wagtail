from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext, ugettext_lazy


class SearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
        _placeholder = kwargs.pop('placeholder', None)
        placeholder_suffix = kwargs.pop('placeholder_suffix', "")
        super(SearchForm, self).__init__(*args, **kwargs)
        if _placeholder is not None:
            placeholder = _placeholder
        else:
            placeholder = 'Search {0}'.format(placeholder_suffix)
        self.fields['q'].widget.attrs = {'placeholder': placeholder}

    q = forms.CharField(label=_("Search term"), widget=forms.TextInput())


class ExternalLinkChooserForm(forms.Form):
    url = forms.URLField(required=True)


class ExternalLinkChooserWithLinkTextForm(forms.Form):
    url = forms.URLField(required=True)
    link_text = forms.CharField(required=True)


class EmailLinkChooserForm(forms.Form):
    email_address = forms.EmailField(required=True)


class EmailLinkChooserWithLinkTextForm(forms.Form):
    email_address = forms.EmailField(required=True)
    link_text = forms.CharField(required=False)


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={'tabindex': '1',}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': ugettext_lazy("Enter password"),
                                          'tabindex': '2',
                                          }),
    )

    def __init__(self, request=None, *args, **kwargs):
        super(LoginForm, self).__init__(request=request, *args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = ugettext_lazy("Enter your %s") % self.username_field.verbose_name



class PasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label=ugettext_lazy("Enter your email address to reset your password"), max_length=254)

    def clean(self):
        cleaned_data = super(PasswordResetForm, self).clean()

        # Find users of this email address
        UserModel = get_user_model()
        email = cleaned_data.get('email')
        if not email:
            raise forms.ValidationError(_("Please fill your email address."))
        active_users = UserModel._default_manager.filter(email__iexact=email, is_active=True)

        if active_users.exists():
            # Check if all users of the email address are LDAP users (and give an error if they are)
            found_non_ldap_user = False
            for user in active_users:
                if user.has_usable_password():
                    found_non_ldap_user = True
                    break

            if not found_non_ldap_user:
                # All found users are LDAP users, give error message
                raise forms.ValidationError(_("Sorry, you cannot reset your password here as your user account is managed by another server."))
        else:
            # No user accounts exist
            raise forms.ValidationError(_("This email address is not recognised."))

        return cleaned_data


class CopyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # CopyPage must be passed a 'page' kwarg indicating the page to be copied
        self.page = kwargs.pop('page')
        can_publish = kwargs.pop('can_publish')
        super(CopyForm, self).__init__(*args, **kwargs)

        self.fields['new_title'] = forms.CharField(initial=self.page.title, label=_("New title"))
        self.fields['new_slug'] = forms.SlugField(initial=self.page.slug, label=_("New slug"))

        pages_to_copy = self.page.get_descendants(inclusive=True)
        subpage_count = pages_to_copy.count() - 1
        if subpage_count > 0:
            self.fields['copy_subpages'] = forms.BooleanField(
                required=False, initial=True, label=_("Copy subpages"),
                help_text=ungettext(
                    "This will copy %(count)s subpage.",
                    "This will copy %(count)s subpages.",
                subpage_count) % {'count': subpage_count})

        if can_publish:
            pages_to_publish_count = pages_to_copy.live().count()
            if pages_to_publish_count > 0:
                # In the specific case that there are no subpages, customise the field label and help text
                if subpage_count == 0:
                    label = _("Publish copied page")
                    help_text = _("This page is live. Would you like to publish its copy as well?")
                else:
                    label = _("Publish copies")
                    help_text = ungettext(
                        "%(count)s of the pages being copied is live. Would you like to publish its copy?",
                        "%(count)s of the pages being copied are live. Would you like to publish their copies?",
                    pages_to_publish_count) % {'count': pages_to_publish_count}

                self.fields['publish_copies'] = forms.BooleanField(
                    required=False, initial=True, label=label, help_text=help_text
                )

    def clean_new_slug(self):
        # Make sure the slug isn't already in use
        slug = self.cleaned_data['new_slug']

        if self.page.get_siblings(inclusive=True).filter(slug=slug).count():
            raise forms.ValidationError(_("This slug is already in use"))
        return slug


class PageViewRestrictionForm(forms.Form):
    restriction_type = forms.ChoiceField(label="Visibility", choices=[
        ('none', ugettext_lazy("Public")),
        ('password', ugettext_lazy("Private, accessible with the following password")),
    ], widget=forms.RadioSelect)
    password = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(PageViewRestrictionForm, self).clean()

        if cleaned_data.get('restriction_type') == 'password' and not cleaned_data.get('password'):
            self._errors["password"] = self.error_class([_('This field is required.')])
            del cleaned_data['password']

        return cleaned_data
