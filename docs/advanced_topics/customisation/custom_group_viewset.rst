Custom group edit/create page
=============================

Custom group edit/create page example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This example shows how to customize group 'edit' and 'create' page in Wagtail
admin.

Let's say you need to connect Active Directory groups with Django groups.
So create a model for Active Directory groups.

.. code-block:: python

  from django.contrib.auth.models import Group
  from django.db import models


  class ADGroup(models.Model):
      guid = models.CharField(verbose_name="GUID", max_length=64, db_index=True, unique=True)
      name = models.CharField(verbose_name="Group", max_length=255)
      domain = models.CharField(verbose_name="Domain", max_length=255, db_index=True)
      description = models.TextField(verbose_name="Description", blank=True, null=True)
      roles = models.ManyToManyField(Group, verbose_name="Role", related_name="adgroups", blank=True)

    class Meta:
        verbose_name = "AD group"
        verbose_name_plural = "AD groups"

However, there is no role field on the Wagtail group 'edit' or 'create' page.
To add it, inherit from Wagtail group form and add a new field.

.. code-block:: python

  from django import forms

  from wagtail.users.forms import GroupForm as WagtailGroupForm

  from .models import ADGroup


  class GroupForm(WagtailGroupForm):
      adgroups = forms.ModelMultipleChoiceField(
          label="AD groups",
          required=False,
          queryset=ADGroup.objects.order_by("name"),
      )

      class Meta(WagtailGroupForm.Meta):
          fields = WagtailGroupForm.Meta.fields + ("adgroups",)

      def __init__(self, initial=None, instance=None, **kwargs):
          if instance is not None:
              if initial is None:
                  initial = {}
              initial["adgroups"] = instance.adgroups.all()
          super().__init__(initial=initial, instance=instance, **kwargs)

      def save(self, commit=True):
          instance = super().save()
          instance.adgroups.set(self.cleaned_data["adgroups"])
          return instance

Now add your custom form into group viewset by inheriting default Wagtail
``GroupViewSet`` class and overriding ``get_form_class`` method.

.. code-block:: python

  from wagtail.users.views.groups import GroupViewSet as WagtailGroupViewSet

  from .forms import GroupForm


  class GroupViewSet(WagtailGroupViewSet):
      def get_form_class(self, for_update=False):
          return GroupForm

Append the field into group 'edit'/'create' templates.

.. code-block:: html+Django

  {% extends "wagtailusers/groups/edit.html" %}
  {% load wagtailusers_tags wagtailadmin_tags i18n %}

  {% block extra_fields %}
      {% include "wagtailadmin/shared/field_as_li.html" with field=form.adgroups %}
  {% endblock extra_fields %}

Finally configure ``wagtail.users`` application for using the viewset. Create
``myapplication/apps.py`` module in the main application package and configure
``AppConfig``.

.. code-block:: python

  from wagtail.users.apps import WagtailUsersAppConfig


  class CustomUsersAppConfig(WagtailUsersAppConfig):
      group_viewset = "myapplication.someapp.viewsets.GroupViewSet"

And put path to ``CustomUsersAppConfig`` into ``settings.INSTALLED_APPS``
instead of ``wagtail.users``.

.. code-block:: python

  INSTALLED_APPS = [
      ...,
      "myapplication.apps.CustomUsersAppConfig",
      # "wagtail.users",
      ...,
  ]
