from django.contrib.admin.utils import unquote
from django.db import transaction
from django.db.models import F
from django.http import (
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.views.generic import View

from .permissions import PermissionCheckedMixin


class ReorderView(PermissionCheckedMixin, View):
    """View for handling the reordering of model instances that have an order field."""

    model = None
    sort_order_field = None
    permission_required = "change"

    def get_queryset(self):
        return self.model._default_manager.all().order_by(self.sort_order_field)

    def post(self, request, *args, **kwargs):
        item_to_move = get_object_or_404(self.model, pk=unquote(kwargs.get("pk")))
        new_position = request.GET.get("position")

        if new_position is None:
            return HttpResponseBadRequest("Position parameter is required")

        try:
            new_position = int(new_position)
        except ValueError:
            return HttpResponseBadRequest("Position must be an integer")

        queryset = self.get_queryset()
        current_position = list(queryset).index(item_to_move)

        with transaction.atomic():
            # Move other items to make space for the item being moved
            if new_position < current_position:
                queryset.filter(
                    **{
                        f"{self.sort_order_field}__gte": new_position,
                        f"{self.sort_order_field}__lt": current_position,
                    }
                ).update(**{self.sort_order_field: F(self.sort_order_field) + 1})
            elif new_position > current_position:
                queryset.filter(
                    **{
                        f"{self.sort_order_field}__gt": current_position,
                        f"{self.sort_order_field}__lte": new_position,
                    }
                ).update(**{self.sort_order_field: F(self.sort_order_field) - 1})

            # Once the other items have been moved, update the actual item.
            setattr(item_to_move, self.sort_order_field, new_position)
            item_to_move.save(update_fields=[self.sort_order_field])

        return JsonResponse({"success": True})
