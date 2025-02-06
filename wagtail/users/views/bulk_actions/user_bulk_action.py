from django.contrib.auth import get_user_model

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed
from wagtail.users.views.users import get_users_filter_query

User = get_user_model()


class UserBulkAction(PermissionCheckedMixin, BulkAction):
    models = [User]
    permission_policy = ModelPermissionPolicy(User)
    any_permission_required = ["add", "change", "delete"]

    def get_all_objects_in_listing_query(self, parent_id):
        listing_objects = self.model.objects.all().values_list("pk", flat=True)
        if "q" in self.request.GET:
            q = self.request.GET.get("q")
            if class_is_indexed(self.model):
                search_backend = get_search_backend()
                listing_objects = search_backend.search(
                    q, User.objects.filter(self.group_filter)
                )
            else:
                model_fields = {f.name for f in self.model._meta.get_fields()}
                conditions = get_users_filter_query(q, model_fields)

                listing_objects = listing_objects.filter(conditions)

        return listing_objects
