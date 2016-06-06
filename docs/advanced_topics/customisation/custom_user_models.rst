Custom user models
==================

Custom user forms example
^^^^^^^^^^^^^^^^^^^^^^^^^

This example shows how to add a text field and foreign key field to a custom user model
and configure Wagtail user forms to allow the fields values to be updated.

Create a custom user model. In this case we extend the ``AbstractUser`` class and add
two fields. The foreign key references another model (not shown).

.. code-block:: python

  class User(AbstractUser):
      country = models.CharField(verbose_name='country', max_length=255)
      status = models.ForeignKey(MembershipStatus, on_delete=models.SET_NULL, null=True, default=1)

Add the app containing your user model to ``INSTALLED_APPS`` and set AUTH_USER_MODEL_ to reference
your model. In this example the app is called ``users`` and the model is ``User``

.. code-block:: python

  AUTH_USER_MODEL = 'users.User'

Create your custom user create and edit forms in your app:

.. code-block:: python

  from django import forms
  from django.utils.translation import ugettext_lazy as _

  from wagtail.wagtailusers.forms import UserEditForm, UserCreationForm

  from users.models import MembershipStatus


  class CustomUserEditForm(UserEditForm):
      country = forms.CharField(required=True, label=_("Country"))
      status = forms.ModelChoiceField(queryset=MembershipStatus.objects, required=True, label=_("Status"))


  class CustomUserCreationForm(UserCreationForm):
      country = forms.CharField(required=True, label=_("Country"))
      status = forms.ModelChoiceField(queryset=MembershipStatus.objects, required=True, label=_("Status"))


Extend the Wagtail user create and edit templates. These extended template should be placed in a
template directory ``wagtailusers/users``.

Template create.html:

.. code-block:: html+django

  {% extends "wagtailusers/users/create.html" %}

  {% block extra_fields %}
      {% include "wagtailadmin/shared/field_as_li.html" with field=form.country %}
      {% include "wagtailadmin/shared/field_as_li.html" with field=form.status %}
  {% endblock extra_fields %}

.. note::
   Using ``{% extends %}`` in this way on a template you're currently overriding is only supported in Django 1.9 and above. On Django 1.8, you will need to use `django-overextends <https://github.com/stephenmcd/django-overextends>`_ instead.

Template edit.html:

.. code-block:: html+django

  {% extends "wagtailusers/users/edit.html" %}

  {% block extra_fields %}
      {% include "wagtailadmin/shared/field_as_li.html" with field=form.country %}
      {% include "wagtailadmin/shared/field_as_li.html" with field=form.status %}
  {% endblock extra_fields %}

The ``extra_fields`` block allows fields to be inserted below the last name field
in the default templates. Other block overriding options exist to allow appending
fields to the end or beginning of the existing fields, or to allow all the fields to
be redefined.

Add the wagtail settings to your project to reference the user form additions:

.. code-block:: python

  WAGTAIL_USER_EDIT_FORM = 'users.forms.CustomUserEditForm'
  WAGTAIL_USER_CREATION_FORM = 'users.forms.CustomUserCreationForm'
  WAGTAIL_USER_CUSTOM_FIELDS = ['country', 'status']


.. _AUTH_USER_MODEL: https://docs.djangoproject.com/en/dev/topics/auth/customizing/#substituting-a-custom-user-model
