from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.move_page import MovePageAction
from wagtail.models import Page

from .base import APIAction


class MovePageAPIActionSerializer(Serializer):
    destination_page_id = fields.IntegerField(required=True)
    position = fields.ChoiceField(
        required=False,
        choices=[
            "left",
            "right",
            "first-child",
            "last-child",
            "first-sibling",
            "last-sibling",
        ],
    )


class MovePageAPIAction(APIAction):
    serializer = MovePageAPIActionSerializer

    def _action_from_data(self, instance, data):
        destination_page_id = data["destination_page_id"]
        target = get_object_or_404(Page, id=destination_page_id)

        return MovePageAction(
            page=instance,
            target=target,
            pos=data.get("position"),
            user=self.request.user,
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)

        instance.refresh_from_db()
        serializer = self.view.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
