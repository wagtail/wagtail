from django.db import migrations, models
import wagtail.fields

class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0040_page_draft_title"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomePage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        on_delete=models.CASCADE,
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.Page",
                    ),
                ),
                (
                    "body",
                    wagtail.fields.RichTextField(blank=True),
                
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
    ]
