from django.contrib.admin.utils import unquote
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
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
        item_to_move = get_object_or_404(self.model, pk=unquote(str(kwargs.get("pk"))))

        try:
            # Position is an index in the list of items,
            # not a value of the sort_order_field.
            new_position = int(request.GET.get("position", ""))
        except ValueError:
            new_position = -1

        queryset = self.get_queryset()
        items = list(queryset.values("pk", self.sort_order_field))

        # If position is missing or not a valid integer, move to the end
        if new_position < 0 or new_position >= len(items):
            new_position = len(items) - 1

        # Get the current sort_order_field value of the item being moved,
        # to be used as the relative anchor for updating the other items.
        current_sort_order = getattr(item_to_move, self.sort_order_field)

        # The current position index of the item being moved (may not be the
        # same as the sort_order_field value), to be used to determine
        # whether to move items up or down.
        current_position = next(
            (i for i, obj in enumerate(items) if obj["pk"] == item_to_move.pk),
            current_sort_order,
        )

        # The sort_order_field value of the item at the new position, which
        # will be set as the new sort_order_field value for the item being moved.
        sort_order_at_position = items[new_position][self.sort_order_field]

        with transaction.atomic():
            if new_position < current_position:
                # We are moving the item up in the list, so we need to push down
                # the items from the new position and below.
                queryset.filter(
                    **{
                        f"{self.sort_order_field}__gte": sort_order_at_position,
                        f"{self.sort_order_field}__lt": current_sort_order,
                    }
                ).update(**{self.sort_order_field: F(self.sort_order_field) + 1})
            elif new_position > current_position:
                # We are moving the item down in the list, so we need to pull up
                # the items from the new position and above.
                queryset.filter(
                    **{
                        f"{self.sort_order_field}__gt": current_sort_order,
                        f"{self.sort_order_field}__lte": sort_order_at_position,
                    }
                ).update(**{self.sort_order_field: F(self.sort_order_field) - 1})

            if new_position != current_position:
                # Once the other items have been moved, update the actual item.
                setattr(item_to_move, self.sort_order_field, sort_order_at_position)
                item_to_move.save(update_fields=[self.sort_order_field])

        return JsonResponse({"success": True})
