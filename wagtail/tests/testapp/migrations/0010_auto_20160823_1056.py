# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-23 15:56
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0029_unicode_slugfield_dj19"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tests", "0009_defaultstreampage"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomFormPageSubmission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("form_data", models.TextField()),
                (
                    "submit_time",
                    models.DateTimeField(auto_now_add=True, verbose_name="submit time"),
                ),
            ],
            options={"abstract": False, "verbose_name": "form submission"},
        ),
        migrations.CreateModel(
            name="FormFieldWithCustomSubmission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "label",
                    models.CharField(
                        help_text="The label of the form field",
                        max_length=255,
                        verbose_name="label",
                    ),
                ),
                (
                    "field_type",
                    models.CharField(
                        choices=[
                            ("singleline", "Single line text"),
                            ("multiline", "Multi-line text"),
                            ("email", "Email"),
                            ("number", "Number"),
                            ("url", "URL"),
                            ("checkbox", "Checkbox"),
                            ("checkboxes", "Checkboxes"),
                            ("dropdown", "Drop down"),
                            ("radio", "Radio buttons"),
                            ("date", "Date"),
                            ("datetime", "Date/time"),
                        ],
                        max_length=16,
                        verbose_name="field type",
                    ),
                ),
                (
                    "required",
                    models.BooleanField(default=True, verbose_name="required"),
                ),
                (
                    "choices",
                    models.TextField(
                        blank=True,
                        help_text="Comma separated list of choices. Only applicable in checkboxes, radio and dropdown.",
                        verbose_name="choices",
                    ),
                ),
                (
                    "default_value",
                    models.CharField(
                        blank=True,
                        help_text="Default value. Comma separated values supported for checkboxes.",
                        max_length=255,
                        verbose_name="default value",
                    ),
                ),
                (
                    "help_text",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="help text"
                    ),
                ),
            ],
            options={"ordering": ["sort_order"], "abstract": False},
        ),
        migrations.CreateModel(
            name="FormPageWithCustomSubmission",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                (
                    "to_address",
                    models.CharField(
                        blank=True,
                        help_text="Optional - form submissions will be emailed to these addresses. Separate multiple addresses by comma.",
                        max_length=255,
                        verbose_name="to address",
                    ),
                ),
                (
                    "from_address",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="from address"
                    ),
                ),
                (
                    "subject",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="subject"
                    ),
                ),
                ("intro", wagtail.core.fields.RichTextField(blank=True)),
                ("thank_you_text", wagtail.core.fields.RichTextField(blank=True)),
            ],
            options={"abstract": False},
            bases=("wagtailcore.page",),
        ),
        migrations.AddField(
            model_name="formfieldwithcustomsubmission",
            name="page",
            field=modelcluster.fields.ParentalKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="custom_form_fields",
                to="tests.FormPageWithCustomSubmission",
            ),
        ),
        migrations.AddField(
            model_name="customformpagesubmission",
            name="page",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="wagtailcore.Page"
            ),
        ),
        migrations.AddField(
            model_name="customformpagesubmission",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
