from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.convert_alias import ConvertAliasPageAction, ConvertAliasPageError
from wagtail.api.v2.utils import BadRequestError

from .base import APIAction


class ConvertAliasPageAPIAction(APIAction):
    serializer = Serializer

    def _action_from_data(self, instance, data):
        return ConvertAliasPageAction(instance, user=self.request.user)

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            new_page = action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)
        except ConvertAliasPageError as e:
            raise BadRequestError(e.args[0])

        serializer = self.view.get_serializer(new_page)
        return Response(serializer.data, status=status.HTTP_200_OK)
