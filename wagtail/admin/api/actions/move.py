from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.core.actions.move_page import MovePageAction
from wagtail.core.models import Page

from .base import APIAction


class MovePageAPIActionSerializer(Serializer):
    target_page_id = fields.IntegerField(required=True)
    position = fields.CharField(required=False)


class MovePageAPIAction(APIAction):
    serializer = MovePageAPIActionSerializer

    def _action_from_data(self, instance, data):
        target_page_id = data["target_page_id"]
        target = get_object_or_404(Page, id=target_page_id)

        return MovePageAction(
            page=instance, target=target, pos=data.get("pos"), user=self.request.user
        )

    def execute(self, instance, data):
        serializer = self.serializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        action = self._action_from_data(instance, serializer.data)

        try:
            action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)

        instance.refresh_from_db()
        serializer = self.view.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
