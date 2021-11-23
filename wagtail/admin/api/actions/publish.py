from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.api.v2.utils import BadRequestError
from wagtail.core.actions.publish_page_revision import PublishPageRevisionAction

from .base import APIAction


class PublishPageAPIActionSerializer(Serializer):
    changed = fields.BooleanField(default=True, required=False)
    log_action = fields.BooleanField(default=True, required=False)
    previous_revision_id = fields.IntegerField(required=False)


class PublishPageAPIAction(APIAction):
    serializer = PublishPageAPIActionSerializer

    def _action_from_data(self, instance, data):
        previous_revision = None
        user = self.request.user
        log_action = data["log_action"]

        previous_revision_id = data.get("previous_revision_id", None)
        if previous_revision_id:
            previous_revision = get_object_or_404(
                instance.revisions, id=previous_revision_id
            )

        revision = instance.save_revision(
            user=user, log_action=log_action, previous_revision=previous_revision
        )

        return PublishPageRevisionAction(
            revision,
            user=user,
            changed=data["changed"],
            log_action=log_action,
            previous_revision=previous_revision,
        )

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
