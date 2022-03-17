from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.publish_page_revision import PublishPageRevisionAction
from wagtail.api.v2.utils import BadRequestError

from .base import APIAction


class PublishPageAPIAction(APIAction):
    serializer = Serializer

    def _action_from_data(self, instance, data):
        user = self.request.user
        revision = instance.get_latest_revision() or instance.save_revision(user=user)
        return PublishPageRevisionAction(revision, user=user)

    def execute(self, instance, data):
        try:
            action = self._action_from_data(instance, data)
        except RuntimeError as e:
            raise BadRequestError(e.args[0])

        try:
            action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)

        new_page = instance.specific_class.objects.get(pk=instance.pk)
        serializer = self.view.get_serializer(new_page)
        return Response(serializer.data, status=status.HTTP_200_OK)
