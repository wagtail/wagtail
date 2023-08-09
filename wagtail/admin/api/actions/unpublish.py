from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.unpublish_page import UnpublishPageAction

from .base import APIAction


class UnpublishPageAPIActionSerializer(Serializer):
    recursive = fields.BooleanField(default=False, required=False)


class UnpublishPageAPIAction(APIAction):
    serializer = UnpublishPageAPIActionSerializer

    def _action_from_data(self, instance, data):
        return UnpublishPageAction(
            page=instance,
            user=self.request.user,
            include_descendants=data["recursive"],
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)

        serializer = self.view.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
