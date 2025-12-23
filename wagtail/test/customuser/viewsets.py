from wagtail.users.views.users import UserViewSet as WagtailUserViewSet

from .forms import CustomUserCreationForm, CustomUserEditForm


class CustomUserViewSet(WagtailUserViewSet):
    icon = "custom-icon"

    def get_form_class(self, for_update=False):
        if for_update:
            return CustomUserEditForm
        return CustomUserCreationForm
