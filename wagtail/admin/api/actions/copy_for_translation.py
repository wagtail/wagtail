from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.copy_for_translation import (
    CopyPageForTranslationAction,
    ParentNotTranslatedError,
)
from wagtail.api.v2.utils import BadRequestError
from wagtail.models.i18n import Locale

from .base import APIAction


class CopyForTranslationAPIActionSerializer(Serializer):
    locale = fields.CharField(max_length=100)
    copy_parents = fields.BooleanField(default=False, required=False)
    alias = fields.BooleanField(default=False, required=False)
    recursive = fields.BooleanField(default=False, required=False)


class CopyForTranslationAPIAction(APIAction):
    serializer = CopyForTranslationAPIActionSerializer

    def _action_from_data(self, instance, data):
        locale = get_object_or_404(Locale, language_code=data["locale"])

        return CopyPageForTranslationAction(
            page=instance,
            locale=locale,
            copy_parents=data["copy_parents"],
            alias=data["alias"],
            user=self.request.user,
            include_subtree=data["recursive"],
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            translated_page = action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)
        except ParentNotTranslatedError as e:
            raise BadRequestError(e.args[0])

        serializer = self.view.get_serializer(translated_page)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
