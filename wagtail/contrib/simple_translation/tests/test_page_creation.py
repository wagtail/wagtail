from django.test import TestCase, override_settings

from wagtail.models import Locale, Page
from wagtail.test.i18n.models import TestPage
from wagtail.test.utils import WagtailTestUtils


@override_settings(
    WAGTAIL_I18N_ENABLED=True,
    WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True,
)
class TestProgrammaticPageCreation(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root = Page.get_first_root_node()
        self.en = Locale.objects.get(language_code="en")
        self.fr = Locale.objects.create(language_code="fr")

    def test_translation_aliases_not_created_outside_admin(self):
        page = self.root.add_child(
            instance=TestPage(
                title="Programmatic page",
                slug="programmatic-page",
                locale=self.en,
            )
        )

        page.save()

        self.assertFalse(
            Page.objects.filter(
                alias_of_id=page.id,
                locale=self.fr,
            ).exists(),
            (
                "Translation aliases are only created via admin hooks. "
                "Programmatic page creation does not create aliases. "
                "See issue #13698."
            ),
        )
