from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.core.actions.unpublish_page import UnpublishPageAction

from .base import APIAction


class UnpublishPageAPIActionSerializer(Serializer):
    set_expired = fields.BooleanField(default=False, required=False)
    log_action = fields.BooleanField(default=True, required=False)


class UnpublishPageAPIAction(APIAction):
    serializer = UnpublishPageAPIActionSerializer

    def _action_from_data(self, instance, data):
        return UnpublishPageAction(
            page=instance,
            set_expired=data["set_expired"],
            log_action=data["log_action"],
            user=self.request.user,
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)

        serializer = self.view.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)
