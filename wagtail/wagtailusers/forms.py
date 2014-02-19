from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.utils.translation import ugettext_lazy as _


# extend Django's UserCreationForm with an 'is_superuser' field
class UserCreationForm(BaseUserCreationForm):

    required_css_class = "required"
    is_superuser = forms.BooleanField(
        label=_("Administrator"),
        required=False,
        help_text=_("If ticked, this user has the ability to manage user accounts.")
    )
    
    email = forms.EmailField(required=True, label=_("Email"))
    first_name = forms.CharField(required=True, label=_("First Name"))
    last_name = forms.CharField(required=True, label=_("Last Name"))

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_superuser", "groups")
        widgets = {
            'groups': forms.CheckboxSelectMultiple
        }

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)

        # users can access django-admin iff they are a superuser
        user.is_staff = user.is_superuser

        if commit:
            user.save()
            self.save_m2m()
        return user


# Largely the same as django.contrib.auth.forms.UserCreationForm, but with enough subtle changes
# (to make password non-required) that it isn't worth inheriting...
class UserEditForm(forms.ModelForm):
    required_css_class = "required"

    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    username = forms.RegexField(
        label=_("Username"),
        max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text=_("Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")
        })

    email = forms.EmailField(required=True, label=_("Email"))
    first_name = forms.CharField(required=True, label=_("First Name"))
    last_name = forms.CharField(required=True, label=_("Last Name"))

    password1 = forms.CharField(
        label=_("Password"),
        required=False,
        widget=forms.PasswordInput,
        help_text=_("Leave blank if not changing."))
    password2 = forms.CharField(
        label=_("Password confirmation"), required=False,
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    is_superuser = forms.BooleanField(
        label=_("Administrator"),
        required=False,
        help_text=_("Administrators have the ability to manage user accounts.")
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "is_active", "is_superuser", "groups")
        widgets = {
            'groups': forms.CheckboxSelectMultiple
        }

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User._default_manager.exclude(id=self.instance.id).get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super(UserEditForm, self).save(commit=False)

        # users can access django-admin iff they are a superuser
        user.is_staff = user.is_superuser

        if self.cleaned_data["password1"]:
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
        return user
