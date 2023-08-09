from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.create_alias import (
    CreatePageAliasAction,
    CreatePageAliasIntegrityError,
)
from wagtail.api.v2.utils import BadRequestError
from wagtail.models import Page

from .base import APIAction


class CreatePageAliasAPIActionSerializer(Serializer):
    destination_page_id = fields.IntegerField(required=False)
    recursive = fields.BooleanField(default=False, required=False)
    update_slug = fields.CharField(required=False)


class CreatePageAliasAPIAction(APIAction):
    serializer = CreatePageAliasAPIActionSerializer

    def _action_from_data(self, instance, data):
        parent, destination_page_id = None, data.get("destination_page_id")
        if destination_page_id:
            parent = get_object_or_404(Page, id=destination_page_id).specific

        return CreatePageAliasAction(
            page=instance,
            recursive=data["recursive"],
            parent=parent,
            update_slug=data.get("update_slug"),
            user=self.request.user,
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            new_page = action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)
        except CreatePageAliasIntegrityError as e:
            raise BadRequestError(e.args[0])

        serializer = self.view.get_serializer(new_page)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
