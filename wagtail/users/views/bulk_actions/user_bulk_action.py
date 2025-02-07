from django.contrib.auth import get_user_model
from django.db.models import Q

from wagtail.admin.views.bulk_action import BulkAction
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.search.backends import get_search_backend
from wagtail.search.index import class_is_indexed

User = get_user_model()


class UserBulkAction(PermissionCheckedMixin, BulkAction):
    models = [User]
    permission_policy = ModelPermissionPolicy(User)
    any_permission_required = ["add", "change", "delete"]

    def get_all_objects_in_listing_query(self, parent_id):
        listing_objects = self.model.objects.all().values_list("pk", flat=True)

        if q := self.request.GET.get("q"):
            if class_is_indexed(self.model):
                search_backend = get_search_backend()
                return search_backend.autocomplete(q, listing_objects)

            model_fields = {f.name for f in self.model._meta.get_fields()}
            filterable_fields = {"username", "first_name", "last_name", "email"}
            common_fields = model_fields & filterable_fields
            conditions = Q()
            for field in common_fields:
                conditions |= Q(**{f"{field}__icontains": q})
            return listing_objects.filter(conditions)

        return listing_objects
