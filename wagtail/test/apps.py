from wagtail.users.apps import WagtailUsersAppConfig


class CustomUsersAppConfig(WagtailUsersAppConfig):
    user_viewset = "wagtail.test.customuser.viewsets.CustomUserViewSet"
