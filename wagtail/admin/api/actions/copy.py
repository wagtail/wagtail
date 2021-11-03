from django.shortcuts import get_object_or_404
from rest_framework import fields
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from wagtail.api.v2.utils import BadRequestError
from wagtail.core.actions.copy_page import AliasPagesMustBeKeptLive, CannotRecursivelyCopyIntoSelf, CopyPageAction, PageCopyError, PageTypeCannotBeCreatedAtDestination, SlugInUse, UserCannotCreateAtDestination, UserCannotPublishAtDestination
from wagtail.core.models import Page

from .base import APIAction


class CopyPageAPIActionSerializer(Serializer):
    # Note: CopyPageAction will validate the destination page
    destination_page_id = fields.IntegerField(required=False)
    recursive = fields.BooleanField(default=False, required=False)
    keep_live = fields.BooleanField(default=True, required=False)
    alias = fields.BooleanField(default=False, required=False)
    slug = fields.CharField(required=False)
    title = fields.CharField(required=False)


class CopyPageAPIAction(APIAction):
    serializer = CopyPageAPIActionSerializer

    def _action_from_data(self, instance, data):
        destination_page_id = data.get('destination_page_id')
        if destination_page_id is None:
            destination = instance.get_parent()
        else:
            destination = get_object_or_404(Page, id=destination_page_id)

        return CopyPageAction(
            user=self.request.user,
            page=instance,
            destination=destination,
            recursive=data['recursive'],
            keep_live=data['keep_live'],
            alias=data['alias'],
            slug=data.get('slug'),
            title=data.get('title'),
        )

    def execute(self, instance, data):
        action = self._action_from_data(instance, data)

        try:
            new_page = action.execute()
        except CannotRecursivelyCopyIntoSelf:
            raise BadRequestError("cannot recursively copy into self")
        except UserCannotCreateAtDestination:
            raise BadRequestError("you do not have permission to create pages at the destination")
        except UserCannotPublishAtDestination:
            raise BadRequestError("you do not have permission to publish pages at the destination")
        except PageTypeCannotBeCreatedAtDestination:
            raise BadRequestError("pages with this type cannot be created at the destination")
        except SlugInUse:
            raise BadRequestError("a page is already using the requested slug at the destination")
        except AliasPagesMustBeKeptLive:
            raise BadRequestError("keep_live cannot be false when alias is true")

        serializer = self.view.get_serializer(new_page)
        return Response(serializer.data)
