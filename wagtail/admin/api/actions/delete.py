from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.delete_page import DeletePageAction

from .base import APIAction


class DeletePageAPIAction(APIAction):
    serializer = Serializer

    def _action_from_data(self, instance, data):
        return DeletePageAction(page=instance, user=self.request.user)

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)

        return Response(status=status.HTTP_204_NO_CONTENT)
