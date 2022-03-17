from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.revert_to_page_revision import (
    RevertToPageRevisionAction,
    RevertToPageRevisionError,
)
from wagtail.api.v2.utils import BadRequestError

from .base import APIAction


class RevertToPageRevisionAPIActionSerializer(Serializer):
    revision_id = fields.IntegerField()


class RevertToPageRevisionAPIAction(APIAction):
    serializer = RevertToPageRevisionAPIActionSerializer

    def _action_from_data(self, instance, data):
        revision = get_object_or_404(instance.revisions, id=data["revision_id"])

        return RevertToPageRevisionAction(
            page=instance, revision=revision, user=self.request.user
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            new_revision = action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)
        except RevertToPageRevisionError as e:
            raise BadRequestError(e.args[0])

        serializer = self.view.get_serializer(new_revision.as_page_object())
        return Response(serializer.data, status=status.HTTP_200_OK)
