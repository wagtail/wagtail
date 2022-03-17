from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import fields, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.actions.copy_page import CopyPageAction, CopyPageIntegrityError
from wagtail.api.v2.utils import BadRequestError
from wagtail.coreutils import find_available_slug
from wagtail.models import Page

from .base import APIAction


class CopyPageAPIActionSerializer(Serializer):
    # Note: CopyPageAction will validate the destination page
    destination_page_id = fields.IntegerField(required=False)
    recursive = fields.BooleanField(default=False, required=False)
    keep_live = fields.BooleanField(default=True, required=False)
    slug = fields.CharField(required=False)
    title = fields.CharField(required=False)


class CopyPageAPIAction(APIAction):
    serializer = CopyPageAPIActionSerializer

    def _action_from_data(self, instance, data):
        destination_page_id = data.get("destination_page_id")
        if destination_page_id is None:
            destination = instance.get_parent()
        else:
            destination = get_object_or_404(Page, id=destination_page_id)

        update_attrs = {}
        if "slug" in data:
            update_attrs["slug"] = data["slug"]
        else:
            # If user didn't specify a particular slug, find an available one
            available_slug = find_available_slug(destination, instance.slug)
            if available_slug != instance.slug:
                update_attrs["slug"] = available_slug

        if "title" in data:
            update_attrs["title"] = data["title"]

        return CopyPageAction(
            page=instance,
            to=destination,
            recursive=data["recursive"],
            keep_live=data["keep_live"],
            update_attrs=update_attrs,
            user=self.request.user,
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            new_page = action.execute()
        except DjangoValidationError as e:
            raise ValidationError(e.message_dict)
        except CopyPageIntegrityError as e:
            raise BadRequestError(e.args[0])

        serializer = self.view.get_serializer(new_page)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
