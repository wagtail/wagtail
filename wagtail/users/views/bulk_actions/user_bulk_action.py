from django.contrib.auth import get_user_model
from django.db.models import Q

from wagtail.admin.views.bulk_action import BulkAction


class UserBulkAction(BulkAction):
    models = [get_user_model()]

    def get_all_objects_in_listing_query(self, parent_id):
        _objects = self.model.objects.all()
        if 'q' in self.request.GET:
            q = self.request.GET.get('q')
            conditions = Q()
            model_fields = [f.name for f in self.model._meta.get_fields()]

            for term in q.split():
                if 'username' in model_fields:
                    conditions |= Q(username__icontains=term)

                if 'first_name' in model_fields:
                    conditions |= Q(first_name__icontains=term)

                if 'last_name' in model_fields:
                    conditions |= Q(last_name__icontains=term)

                if 'email' in model_fields:
                    conditions |= Q(email__icontains=term)

            _objects = _objects.filter(conditions)

        listing_objects = []
        for obj in _objects:
            listing_objects.append(obj.pk)

        return listing_objects
