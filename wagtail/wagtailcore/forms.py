from django import forms


class PasswordPageViewRestrictionForm(forms.Form):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    return_url = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.restriction = kwargs.pop('instance')
        super(PasswordPageViewRestrictionForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        data = self.cleaned_data['password']
        if data != self.restriction.password:
            raise forms.ValidationError("The password you have entered is not correct. Please try again.")

        return data
