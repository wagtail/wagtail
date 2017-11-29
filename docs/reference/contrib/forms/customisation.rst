Form builder customisation
==========================

For a basic usage example see :ref:`form_builder_usage`.

Custom ``related_name`` for form fields
---------------------------------------

If you want to change ``related_name`` for form fields
(by default ``AbstractForm`` and ``AbstractEmailForm`` expect ``form_fields`` to be defined),
you will need to override the ``get_form_fields`` method.
You can do this as shown below.

.. code-block:: python

    from modelcluster.fields import ParentalKey
    from wagtail.admin.edit_handlers import (
        FieldPanel, FieldRowPanel,
        InlinePanel, MultiFieldPanel
    )
    from wagtail.core.fields import RichTextField
    from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField


    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='custom_form_fields')


    class FormPage(AbstractEmailForm):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

        content_panels = AbstractEmailForm.content_panels + [
            FieldPanel('intro', classname="full"),
            InlinePanel('custom_form_fields', label="Form fields"),
            FieldPanel('thank_you_text', classname="full"),
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
            ], "Email"),
        ]

        def get_form_fields(self):
            return self.custom_form_fields.all()

Custom form submission model
----------------------------

If you need to save additional data, you can use a custom form submission model.
To do this, you need to:

* Define a model that extends ``wagtail.contrib.forms.models.AbstractFormSubmission``.
* Override the ``get_submission_class`` and ``process_form_submission`` methods in your page model.

Example:

.. code-block:: python

    import json

    from django.conf import settings
    from django.core.serializers.json import DjangoJSONEncoder
    from django.db import models
    from modelcluster.fields import ParentalKey
    from wagtail.admin.edit_handlers import (
        FieldPanel, FieldRowPanel,
        InlinePanel, MultiFieldPanel
    )
    from wagtail.core.fields import RichTextField
    from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField, AbstractFormSubmission


    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')


    class FormPage(AbstractEmailForm):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

        content_panels = AbstractEmailForm.content_panels + [
            FieldPanel('intro', classname="full"),
            InlinePanel('form_fields', label="Form fields"),
            FieldPanel('thank_you_text', classname="full"),
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
            ], "Email"),
        ]

        def get_submission_class(self):
            return CustomFormSubmission

        def process_form_submission(self, form):
            self.get_submission_class().objects.create(
                form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
                page=self, user=form.user
            )


    class CustomFormSubmission(AbstractFormSubmission):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


Add custom data to CSV export
-----------------------------

If you want to add custom data to the CSV export, you will need to:

* Override the ``get_data_fields`` method in page model.
* Override ``get_data`` in the submission model.

The following example shows how to add a username to the CSV export:

.. code-block:: python

    import json

    from django.conf import settings
    from django.core.serializers.json import DjangoJSONEncoder
    from django.db import models
    from modelcluster.fields import ParentalKey
    from wagtail.admin.edit_handlers import (
        FieldPanel, FieldRowPanel,
        InlinePanel, MultiFieldPanel
    )
    from wagtail.core.fields import RichTextField
    from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField, AbstractFormSubmission


    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')


    class FormPage(AbstractEmailForm):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

        content_panels = AbstractEmailForm.content_panels + [
            FieldPanel('intro', classname="full"),
            InlinePanel('form_fields', label="Form fields"),
            FieldPanel('thank_you_text', classname="full"),
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
            ], "Email"),
        ]

        def get_data_fields(self):
            data_fields = [
                ('username', 'Username'),
            ]
            data_fields += super(FormPage, self).get_data_fields()

            return data_fields

        def get_submission_class(self):
            return CustomFormSubmission

        def process_form_submission(self, form):
            self.get_submission_class().objects.create(
                form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
                page=self, user=form.user
            )


    class CustomFormSubmission(AbstractFormSubmission):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

        def get_data(self):
            form_data = super(CustomFormSubmission, self).get_data()
            form_data.update({
                'username': self.user.username,
            })

            return form_data


Note that this code also changes the submissions list view.

Check that a submission already exists for a user
-------------------------------------------------

If you want to prevent users from filling in a form more than once,
you need to override the ``serve`` method in your page model.

Example:

.. code-block:: python

    import json

    from django.conf import settings
    from django.core.serializers.json import DjangoJSONEncoder
    from django.db import models
    from django.shortcuts import render
    from modelcluster.fields import ParentalKey
    from wagtail.admin.edit_handlers import (
        FieldPanel, FieldRowPanel,
        InlinePanel, MultiFieldPanel
    )
    from wagtail.core.fields import RichTextField
    from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField, AbstractFormSubmission


    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')


    class FormPage(AbstractEmailForm):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

        content_panels = AbstractEmailForm.content_panels + [
            FieldPanel('intro', classname="full"),
            InlinePanel('form_fields', label="Form fields"),
            FieldPanel('thank_you_text', classname="full"),
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
            ], "Email"),
        ]

        def serve(self, request, *args, **kwargs):
            if self.get_submission_class().objects.filter(page=self, user__pk=request.user.pk).exists():
                return render(
                    request,
                    self.template,
                    self.get_context(request)
                )

            return super(FormPage, self).serve(request, *args, **kwargs)

        def get_submission_class(self):
            return CustomFormSubmission

        def process_form_submission(self, form):
            self.get_submission_class().objects.create(
                form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
                page=self, user=form.user
            )


    class CustomFormSubmission(AbstractFormSubmission):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

        class Meta:
            unique_together = ('page', 'user')


Your template should look like this:

.. code-block:: django

    {% load wagtailcore_tags %}
    <html>
        <head>
            <title>{{ page.title }}</title>
        </head>
        <body>
            <h1>{{ page.title }}</h1>

            {% if user.is_authenticated and user.is_active or request.is_preview %}
                {% if form %}
                    <div>{{ page.intro|richtext }}</div>
                    <form action="{% pageurl page %}" method="POST">
                        {% csrf_token %}
                        {{ form.as_p }}
                        <input type="submit">
                    </form>
                {% else %}
                    <div>You can fill in the from only one time.</div>
                {% endif %}
            {% else %}
                <div>To fill in the form, you must to log in.</div>
            {% endif %}
        </body>
    </html>


Multi-step form
---------------

The following example shows how to create a multi-step form.

.. code-block:: python

    from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
    from django.shortcuts import render
    from modelcluster.fields import ParentalKey
    from wagtail.admin.edit_handlers import (
        FieldPanel, FieldRowPanel,
        InlinePanel, MultiFieldPanel
    )
    from wagtail.core.fields import RichTextField
    from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField


    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')


    class FormPage(AbstractEmailForm):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

        content_panels = AbstractEmailForm.content_panels + [
            FieldPanel('intro', classname="full"),
            InlinePanel('form_fields', label="Form fields"),
            FieldPanel('thank_you_text', classname="full"),
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
            ], "Email"),
        ]

        def get_form_class_for_step(self, step):
            return self.form_builder(step.object_list).get_form_class()

        def serve(self, request, *args, **kwargs):
            """
            Implements a simple multi-step form.

            Stores each step into a session.
            When the last step was submitted correctly, saves whole form into a DB.
            """

            session_key_data = 'form_data-%s' % self.pk
            is_last_step = False
            step_number = request.GET.get('p', 1)

            paginator = Paginator(self.get_form_fields(), per_page=1)
            try:
                step = paginator.page(step_number)
            except PageNotAnInteger:
                step = paginator.page(1)
            except EmptyPage:
                step = paginator.page(paginator.num_pages)
                is_last_step = True

            if request.method == 'POST':
                # The first step will be submitted with step_number == 2,
                # so we need to get a form from previous step
                # Edge case - submission of the last step
                prev_step = step if is_last_step else paginator.page(step.previous_page_number())

                # Create a form only for submitted step
                prev_form_class = self.get_form_class_for_step(prev_step)
                prev_form = prev_form_class(request.POST, page=self, user=request.user)
                if prev_form.is_valid():
                    # If data for step is valid, update the session
                    form_data = request.session.get(session_key_data, {})
                    form_data.update(prev_form.cleaned_data)
                    request.session[session_key_data] = form_data

                    if prev_step.has_next():
                        # Create a new form for a following step, if the following step is present
                        form_class = self.get_form_class_for_step(step)
                        form = form_class(page=self, user=request.user)
                    else:
                        # If there is no next step, create form for all fields
                        form = self.get_form(
                            request.session[session_key_data],
                            page=self, user=request.user
                        )

                        if form.is_valid():
                            # Perform validation again for whole form.
                            # After successful validation, save data into DB,
                            # and remove from the session.
                            form_submission = self.process_form_submission(form)
                            del request.session[session_key_data]
                            # render the landing page
                            return self.render_landing_page(request, form_submission, *args, **kwargs)
                else:
                    # If data for step is invalid
                    # we will need to display form again with errors,
                    # so restore previous state.
                    form = prev_form
                    step = prev_step
            else:
                # Create empty form for non-POST requests
                form_class = self.get_form_class_for_step(step)
                form = form_class(page=self, user=request.user)

            context = self.get_context(request)
            context['form'] = form
            context['fields_step'] = step
            return render(
                request,
                self.template,
                context
            )



Your template for this form page should look like this:

.. code-block:: django

    {% load wagtailcore_tags %}
    <html>
        <head>
            <title>{{ page.title }}</title>
        </head>
        <body>
            <h1>{{ page.title }}</h1>

            <div>{{ page.intro|richtext }}</div>
            <form action="{% pageurl page %}?p={{ fields_step.number|add:"1" }}" method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <input type="submit">
            </form>
        </body>
    </html>


Note that the example shown before allows the user to return to a previous step,
or to open a second step without submitting the first step.
Depending on your requirements, you may need to add extra checks.

Show results
------------

If you are implementing polls or surveys, you may want to show results after submission.
The following example demonstrates how to do this.

First, you need to collect results as shown below:

.. code-block:: python

    from modelcluster.fields import ParentalKey
    from wagtail.admin.edit_handlers import (
        FieldPanel, FieldRowPanel,
        InlinePanel, MultiFieldPanel
    )
    from wagtail.core.fields import RichTextField
    from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField


    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')


    class FormPage(AbstractEmailForm):
        intro = RichTextField(blank=True)
        thank_you_text = RichTextField(blank=True)

        content_panels = AbstractEmailForm.content_panels + [
            FieldPanel('intro', classname="full"),
            InlinePanel('form_fields', label="Form fields"),
            FieldPanel('thank_you_text', classname="full"),
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
            ], "Email"),
        ]

        def get_context(self, request, *args, **kwargs):
            context = super(FormPage, self).get_context(request, *args, **kwargs)

            # If you need to show results only on landing page,
            # you may need check request.method

            results = dict()
            # Get information about form fields
            data_fields = [
                (field.clean_name, field.label)
                for field in self.get_form_fields()
            ]

            # Get all submissions for current page
            submissions = self.get_submission_class().objects.filter(page=self)
            for submission in submissions:
                data = submission.get_data()

                # Count results for each question
                for name, label in data_fields:
                    answer = data.get(name)
                    if answer is None:
                        # Something wrong with data.
                        # Probably you have changed questions
                        # and now we are receiving answers for old questions.
                        # Just skip them.
                        continue

                    if type(answer) is list:
                        # Answer is a list if the field type is 'Checkboxes'
                        answer = u', '.join(answer)

                    question_stats = results.get(label, {})
                    question_stats[answer] = question_stats.get(answer, 0) + 1
                    results[label] = question_stats

            context.update({
                'results': results,
            })
            return context


Next, you need to transform your template to display the results:

.. code-block:: django

    {% load wagtailcore_tags %}
    <html>
        <head>
            <title>{{ page.title }}</title>
        </head>
        <body>
            <h1>{{ page.title }}</h1>

            <h2>Results</h2>
            {% for question, answers in results.items %}
                <h3>{{ question }}</h3>
                {% for answer, count in answers.items %}
                    <div>{{ answer }}: {{ count }}</div>
                {% endfor %}
            {% endfor %}

            <div>{{ page.intro|richtext }}</div>
            <form action="{% pageurl page %}" method="POST">
                {% csrf_token %}
                {{ form.as_p }}
                <input type="submit">
            </form>
        </body>
    </html>


You can also show the results on the landing page.


Custom landing page redirect
----------------------------

You can override the ``render_landing_page`` method on your `FormPage` to change what is rendered when a form submits.

In this example below we have added a `thank_you_page` field that enables custom redirects after a form submits to the selected page.

When overriding the ``render_landing_page`` method, we check if there is a linked `thank_you_page` and then redirect to it if it exists.

Finally, we add a URL param of `id` based on the ``form_submission`` if it exists.

.. code-block:: python

    from django.shortcuts import redirect
    from wagtail.wagtailadmin.edit_handlers import (
        FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel, PageChooserPanel)
    from wagtail.contrib.forms.models import AbstractEmailForm

    class FormPage(AbstractEmailForm):

        # intro, thank_you_text, ...

        thank_you_page = models.ForeignKey(
            'wagtailcore.Page',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+',
        )

        def render_landing_page(self, request, form_submission=None, *args, **kwargs):
            if self.thank_you_page:
                url = self.thank_you_page.url
                # if a form_submission instance is available, append the id to URL
                # when previewing landing page, there will not be a form_submission instance
                if form_submission:
                  url += '?id=%s' % form_submission.id
                return redirect(url, permanent=False)
            # if no thank_you_page is set, render default landing page
            return super(FormPage, self).render_landing_page(request, form_submission, *args, **kwargs)

        content_panels = AbstractEmailForm.content_panels + [
            FieldPanel('intro', classname='full'),
            InlinePanel('form_fields'),
            FieldPanel('thank_you_text', classname='full'),
            PageChooserPanel('thank_you_page'),
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('from_address', classname='col6'),
                    FieldPanel('to_address', classname='col6'),
                ]),
                FieldPanel('subject'),
            ], 'Email'),
        ]


Adding Custom Field Types
-------------------------

Here is how you can add a custom field type, beyond the built in form field choices.

Extend the default ``FORM_FIELD_CHOICES`` by importing and creating a new tuple that has our additional field added, the added items need to be tuples like ('field_type_key', 'Nice Field Label').

In your ``FormField`` model definition, override the ``field_type`` so that we can add the additional field choice to the dropdown.

Create a new class that extends ``FormBuilder``, this will have a method to match the new field type we want to make available, this method must return an instanced Django Form Field.
The name of this method must match the field_type_key for the additional choice added, the format is ``create_<field_type_key>_field``.

Add the ``form_builder`` attribute to your ``FormPage`` method so that this extended form builder is used.

Example code below where we have added a new ``ipaddress`` field type.

.. code-block:: python

    from django.db import models
    from modelcluster.fields import ParentalKey
    from wagtail.contrib.forms.forms import FormBuilder
    from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField, FORM_FIELD_CHOICES

    EXTENDED_CHOICES = FORM_FIELD_CHOICES + (('ipaddress', 'IP Address'),) # remember trailing comma


    class FormField(AbstractFormField):
        page = ParentalKey('FormPage', related_name='form_fields')
        # override the field_type field with extended choices
        field_type = models.CharField(
            verbose_name='field type',
            max_length=16,
            choices=EXTENDED_CHOICES
        )


    # custom form builder class that extends FormBuilder
    class CustomFormBuilder(FormBuilder):
        # create a function that returns an instanced Django form field
        # function name must match create_[field_name]_field
        def create_ipaddress_field(self, field, options):
            return django.forms.GenericIPAddressField(**options)


    class FormPage(AbstractEmailForm):
        # intro, thank_you_text, edit_handlers, etc...

        # use custom form builder defined above
        form_builder = CustomFormBuilder
