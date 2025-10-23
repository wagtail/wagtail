from io import StringIO

from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.test import TestCase
from django.utils.functional import SimpleLazyObject

from wagtail.blocks import StreamValue, StructValue
from wagtail.documents import get_document_model
from wagtail.documents.tests.utils import get_test_document_file
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, ReferenceIndex
from wagtail.rich_text import RichText
from wagtail.test.testapp.models import (
    Advert,
    AdvertWithCustomUUIDPrimaryKey,
    EventPage,
    EventPageCarouselItem,
    EventPageRelatedLink,
    EventPageSpeaker,
    GenericSnippetNoFieldIndexPage,
    GenericSnippetNoIndexPage,
    GenericSnippetPage,
    HeadCountRelatedModelUsingPK,
    ModelWithNullableParentalKey,
    VariousOnDeleteModel,
)


class TestCreateOrUpdateForObject(TestCase):
    def setUp(self):
        with self.captureOnCommitCallbacks(execute=True):
            image_model = get_image_model()
            self.image_content_type = ContentType.objects.get_for_model(image_model)

            self.test_feed_image = image_model.objects.create(
                title="Test feed image",
                file=get_test_image_file(),
            )
            self.test_image_1 = image_model.objects.create(
                title="Test image 1",
                file=get_test_image_file(),
            )
            self.test_image_2 = image_model.objects.create(
                title="Test image 2",
                file=get_test_image_file(),
            )

            # Add event page
            self.event_page = EventPage(
                title="Event page",
                slug="event-page",
                location="the moon",
                audience="public",
                cost="free",
                date_from="2001-01-01",
                feed_image=self.test_feed_image,
            )
            self.event_page.carousel_items = [
                EventPageCarouselItem(
                    caption="1234567", image=self.test_image_1, sort_order=1
                ),
                EventPageCarouselItem(
                    caption="7654321", image=self.test_image_2, sort_order=2
                ),
                EventPageCarouselItem(
                    caption="abcdefg", image=self.test_image_1, sort_order=3
                ),
            ]
            self.root_page = Page.objects.get(id=2)
            self.root_page.add_child(instance=self.event_page)

        self.expected_references = {
            (
                self.image_content_type.id,
                str(self.test_feed_image.pk),
                "feed_image",
                "feed_image",
            ),
            (
                self.image_content_type.id,
                str(self.test_image_1.pk),
                "carousel_items.item.image",
                f"carousel_items.{self.event_page.carousel_items.get(sort_order=1).id}.image",
            ),
            (
                self.image_content_type.id,
                str(self.test_image_2.pk),
                "carousel_items.item.image",
                f"carousel_items.{self.event_page.carousel_items.get(sort_order=2).id}.image",
            ),
            (
                self.image_content_type.id,
                str(self.test_image_1.pk),
                "carousel_items.item.image",
                f"carousel_items.{self.event_page.carousel_items.get(sort_order=3).id}.image",
            ),
        }

    def test(self):
        self.assertSetEqual(
            set(
                ReferenceIndex.get_references_for_object(self.event_page).values_list(
                    "to_content_type", "to_object_id", "model_path", "content_path"
                )
            ),
            self.expected_references,
        )

    def test_update(self):
        reference_to_keep = ReferenceIndex.objects.get(
            base_content_type=ReferenceIndex._get_base_content_type(self.event_page),
            content_type=ContentType.objects.get_for_model(self.event_page),
            content_path="feed_image",
        )
        reference_to_remove = ReferenceIndex.objects.create(
            base_content_type=ReferenceIndex._get_base_content_type(self.event_page),
            content_type=ContentType.objects.get_for_model(self.event_page),
            object_id=self.event_page.pk,
            to_content_type=self.image_content_type,
            to_object_id=self.test_image_1.pk,
            model_path="hero_image",  # Field doesn't exist
            content_path="hero_image",
            content_path_hash=ReferenceIndex._get_content_path_hash("hero_image"),
        )

        ReferenceIndex.create_or_update_for_object(self.event_page)

        # Check that the record for the reference to be kept has been preserved/reused
        self.assertTrue(ReferenceIndex.objects.filter(id=reference_to_keep.id).exists())

        # Check that the record for the reference to be removed has been deleted
        self.assertFalse(
            ReferenceIndex.objects.filter(id=reference_to_remove.id).exists()
        )

        # Check that the current stored references are correct
        self.assertSetEqual(
            set(
                ReferenceIndex.get_references_for_object(self.event_page).values_list(
                    "to_content_type", "to_object_id", "model_path", "content_path"
                )
            ),
            {
                (
                    self.image_content_type.id,
                    str(self.test_feed_image.pk),
                    "feed_image",
                    "feed_image",
                ),
                (
                    self.image_content_type.id,
                    str(self.test_image_1.pk),
                    "carousel_items.item.image",
                    f"carousel_items.{self.event_page.carousel_items.get(sort_order=1).id}.image",
                ),
                (
                    self.image_content_type.id,
                    str(self.test_image_2.pk),
                    "carousel_items.item.image",
                    f"carousel_items.{self.event_page.carousel_items.get(sort_order=2).id}.image",
                ),
                (
                    self.image_content_type.id,
                    str(self.test_image_1.pk),
                    "carousel_items.item.image",
                    f"carousel_items.{self.event_page.carousel_items.get(sort_order=3).id}.image",
                ),
            },
        )

    def test_saving_base_model_does_not_remove_references(self):
        with self.captureOnCommitCallbacks(execute=True):
            page = Page.objects.get(pk=self.event_page.pk)
            page.save()
        self.assertSetEqual(
            set(
                ReferenceIndex.get_references_for_object(self.event_page).values_list(
                    "to_content_type", "to_object_id", "model_path", "content_path"
                )
            ),
            self.expected_references,
        )

    def test_null_parental_key(self):
        with self.captureOnCommitCallbacks(execute=True):
            obj = ModelWithNullableParentalKey(
                content="""<p><a linktype="page" id="%d">event page</a></p>"""
                % self.event_page.id
            )
            obj.save()

        # Models with a ParentalKey are not considered indexable - references are recorded against the parent model
        # instead. Since the ParentalKey is null here, no reference will be recorded.
        refs = ReferenceIndex.get_references_to(self.event_page)
        self.assertEqual(refs.count(), 0)

    def test_lazy_parental_key(self):
        with self.captureOnCommitCallbacks(execute=True):
            event_page_related_link = EventPageRelatedLink()
            # The parent model is a lazy object
            event_page_related_link.page = SimpleLazyObject(lambda: self.event_page)
            event_page_related_link.link_page = self.root_page
            event_page_related_link.save()
        refs = ReferenceIndex.get_references_to(self.root_page)
        self.assertEqual(refs.count(), 1)

    def test_generic_foreign_key(self):
        with self.captureOnCommitCallbacks(execute=True):
            page1 = GenericSnippetPage(
                title="generic snippet page", snippet_content_object=self.event_page
            )
            self.root_page.add_child(instance=page1)
            page2 = GenericSnippetPage(
                title="generic snippet page", snippet_content_object=None
            )
            self.root_page.add_child(instance=page2)

        refs = ReferenceIndex.get_references_to(self.event_page)
        self.assertEqual(refs.count(), 1)

    def test_model_index_ignore_generic_foreign_key(self):
        with self.captureOnCommitCallbacks(execute=True):
            page1 = GenericSnippetNoIndexPage(
                title="generic snippet page", snippet_content_object=self.event_page
            )
            self.root_page.add_child(instance=page1)
            page2 = GenericSnippetNoIndexPage(
                title="generic snippet page", snippet_content_object=None
            )
            self.root_page.add_child(instance=page2)

        # There should be no references
        refs = ReferenceIndex.get_references_to(self.event_page)
        self.assertEqual(refs.count(), 0)

    def test_model_field_index_ignore_generic_foreign_key(self):
        with self.captureOnCommitCallbacks(execute=True):
            content_type = ContentType.objects.get_for_model(self.event_page)
            page1 = GenericSnippetNoFieldIndexPage(
                title="generic snippet page",
                snippet_content_type_nonindexed=content_type,
            )
            self.root_page.add_child(instance=page1)
            page2 = GenericSnippetNoFieldIndexPage(
                title="generic snippet page", snippet_content_type_nonindexed=None
            )
            self.root_page.add_child(instance=page2)

        # There should be no references
        refs = ReferenceIndex.get_references_to(content_type)
        self.assertEqual(refs.count(), 0)

    def test_model_with_uuid_primary_key(self):
        refs = ReferenceIndex.get_references_to(self.event_page)
        self.assertEqual(refs.count(), 0)

        with self.captureOnCommitCallbacks(execute=True):
            AdvertWithCustomUUIDPrimaryKey.objects.create(
                text="An advertisement",
                page=self.event_page,
            )

        refs = ReferenceIndex.get_references_to(self.event_page)
        self.assertEqual(refs.count(), 1)

    def test_rebuild_references_index_no_verbosity(self):
        stdout = StringIO()
        management.call_command(
            "rebuild_references_index",
            verbosity=0,
            stdout=stdout,
        )
        self.assertFalse(stdout.getvalue())

    def test_show_references_index(self):
        stdout = StringIO()
        management.call_command(
            "show_references_index",
            stdout=stdout,
        )
        self.assertIn(" 3  wagtail.images.models.Image", stdout.getvalue())
        self.assertIn(" 4  wagtail.test.testapp.models.EventPage", stdout.getvalue())

    def test_inline_custom_pk_model(self):
        related_page = EventPage(
            title="Related page",
            slug="related-page",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2025-03-21",
        )
        with self.captureOnCommitCallbacks(execute=True):
            self.root_page.add_child(instance=related_page)

        refs = ReferenceIndex.get_references_to(related_page)
        self.assertEqual(refs.count(), 0)

        with self.captureOnCommitCallbacks(execute=True):
            HeadCountRelatedModelUsingPK.objects.create(
                head_count=1234,
                event_page=self.event_page,
                related_page=related_page,
            )

        refs = ReferenceIndex.get_references_to(related_page)
        self.assertEqual(refs.count(), 1)


class TestDescribeOnDelete(TestCase):
    fixtures = ["test.json"]

    @classmethod
    def setUpTestData(cls):
        management.call_command("rebuild_references_index", stdout=StringIO())

    def setUp(self):
        field = VariousOnDeleteModel._meta.get_field("stream_field")
        advertisement_content = field.stream_block.child_blocks["advertisement_content"]
        captioned_advert = advertisement_content.child_blocks["captioned_advert"]

        self.advert = Advert.objects.create(text="An advertisement")
        self.advert_uuid = AdvertWithCustomUUIDPrimaryKey.objects.create(
            text="A UUID advertisement"
        )

        self.page = EventPage.objects.first()
        page_link = f'<p>Link to <a id="{self.page.id}" linktype="page">a page</a></p>'

        self.image = get_image_model().objects.create(
            title="My image",
            file=get_test_image_file(),
        )

        self.document = get_document_model().objects.create(
            title="My document",
            file=get_test_document_file(),
        )

        # Each case is a tuple of (
        #   VariousOnDeleteModel init kwargs,
        #   referred object,
        #   expected field description,
        #   expected on delete description,
        # )
        self.cases = [
            # References from ForeignKey
            (
                {"text": "on_delete=CASCADE", "on_delete_cascade": self.advert},
                self.advert,
                "On delete cascade",
                "the various on delete model will also be deleted",
            ),
            (
                {"text": "on_delete=PROTECT", "on_delete_protect": self.advert},
                self.advert,
                "On delete protect",
                "prevents deletion",
            ),
            (
                {"text": "on_delete=RESTRICT", "on_delete_restrict": self.advert},
                self.advert,
                "On delete restrict",
                "may prevent deletion",
            ),
            (
                {"text": "on_delete=SET_NULL", "on_delete_set_null": self.advert},
                self.advert,
                "On delete set null",
                "will unset the reference",
            ),
            (
                {"text": "on_delete=SET_DEFAULT", "on_delete_set_default": self.advert},
                self.advert,
                "On delete set default",
                "will be set to the default various on delete model",
            ),
            (
                {"text": "on_delete=SET", "on_delete_set": self.advert},
                self.advert,
                "On delete set",
                "will be set to a various on delete model specified by the system",
            ),
            (
                {"text": "on_delete=DO_NOTHING", "on_delete_do_nothing": self.advert},
                self.advert,
                "On delete do nothing",
                "will do nothing",
            ),
            # References from GenericForeignKey
            (
                {"text": "GenericForeignKey", "content_object": self.advert_uuid},
                self.advert_uuid,
                "Content object",
                "will unset the reference",
            ),
            # References from RichTextField
            (
                {"text": "RichTextField model field", "rich_text": page_link},
                self.page,
                "Rich text",
                "will unset the reference",
            ),
            (
                {
                    "text": "deep RichTextBlock",
                    "stream_field": StreamValue(
                        field.stream_block,
                        [
                            (
                                "advertisement_content",
                                StreamValue(
                                    advertisement_content,
                                    [
                                        (
                                            "rich_text",
                                            RichText(page_link),
                                        )
                                    ],
                                ),
                            )
                        ],
                    ),
                },
                self.page,
                "Stream field → Advertisement content → Rich text",
                "will unset the reference",
            ),
            # References from StreamField
            (
                {
                    "text": "deep SnippetChooserBlock",
                    "stream_field": StreamValue(
                        field.stream_block,
                        [
                            (
                                "advertisement_content",
                                StreamValue(
                                    advertisement_content,
                                    [
                                        (
                                            "captioned_advert",
                                            StructValue(
                                                captioned_advert,
                                                [
                                                    ("advert", self.advert),
                                                    ("caption", "Deep text"),
                                                ],
                                            ),
                                        )
                                    ],
                                ),
                            )
                        ],
                    ),
                },
                self.advert,
                "Stream field → Advertisement content → Captioned advert",
                "will unset the reference",
            ),
            (
                {
                    "text": "ImageChooserBlock",
                    "stream_field": StreamValue(
                        field.stream_block, [("image", self.image)]
                    ),
                },
                self.image,
                "Stream field → Image",
                "will unset the reference",
            ),
            (
                {
                    "text": "DocumentChooserBlock",
                    "stream_field": StreamValue(
                        field.stream_block, [("document", self.document)]
                    ),
                },
                self.document,
                "Stream field → Document",
                "will unset the reference",
            ),
        ]

    def test_describe_source_field_and_on_delete(self):
        for (
            init_kwargs,
            referred_object,
            field_description,
            on_delete_description,
        ) in self.cases:
            with self.subTest(test=init_kwargs["text"]):
                # Explicitly pass None to this field so that it is not set to
                # the default value for test cases other than the SET_DEFAULT case
                if "on_delete_set_default" not in init_kwargs:
                    init_kwargs["on_delete_set_default"] = None

                with self.captureOnCommitCallbacks(execute=True):
                    obj = VariousOnDeleteModel.objects.create(**init_kwargs)
                usage = ReferenceIndex.get_references_to(
                    referred_object
                ).group_by_source_object()
                referrer, references = usage[0]
                reference = references[0]

                self.assertIs(usage.is_protected, "on_delete_protect" in init_kwargs)
                self.assertEqual(usage.count(), 1)
                self.assertEqual(referrer, obj)
                self.assertEqual(len(references), 1)
                self.assertEqual(reference.describe_source_field(), field_description)
                self.assertEqual(reference.describe_on_delete(), on_delete_description)
                obj.delete()

    def test_describe_source_field_and_on_delete_parental_key(self):
        # The test fixtures contain two references to the advert:
        # 1. One advert placement on the home page
        # 2. One advert placement on the Christmas page
        advert = Advert.objects.first()
        usage = ReferenceIndex.get_references_to(advert).group_by_source_object()
        self.assertEqual(usage.count(), 2)
        for _, references in usage:
            reference = references[0]
            self.assertEqual(reference.describe_source_field(), "Advert")
            self.assertEqual(
                reference.describe_on_delete(),
                "the advert placement will also be deleted",
            )

    def test_parental_key_with_related_query_name(self):
        # EventPageSpeaker has a ParentalKey to EventPage with a
        # related_query_name that is different from the related_name, which
        # causes a mismatch between the recorded model_path and the way we
        # introspect the source field.
        root_page = Page.objects.get(id=2)
        speaker = EventPageSpeaker(
            first_name="Willie", last_name="Wagtail", link_page=root_page
        )
        event_page = EventPage.objects.first()
        event_page.speakers.add(speaker)
        with self.captureOnCommitCallbacks(execute=True):
            event_page.save()
        refs = ReferenceIndex.get_references_to(root_page)
        self.assertEqual(refs.count(), 1)
        self.assertEqual(refs[0].describe_source_field(), "Link page")
        self.assertEqual(
            refs[0].describe_on_delete(),
            "the event page speaker will also be deleted",
        )

    def test_nonexistent_field(self):
        # Simulate a situation where the field does not exist on the model
        # (e.g. due to a stale reference after the field was removed or renamed)
        reference = ReferenceIndex.objects.create(
            base_content_type=ReferenceIndex._get_base_content_type(self.advert),
            content_type=ContentType.objects.get_for_model(self.advert),
            object_id=self.advert.pk,
            to_content_type=ContentType.objects.get_for_model(self.page),
            to_object_id=self.page.pk,
            model_path="nonexistent_field",
            content_path="some_path",
            content_path_hash=ReferenceIndex._get_content_path_hash("some_path"),
        )
        with self.assertRaises(FieldDoesNotExist):
            reference.describe_source_field()


class TestBulkFetch(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.image_model = get_image_model()
        cls.document_model = get_document_model()

        cls.test_image_1 = cls.image_model.objects.create(
            title="Test image 1",
            file=get_test_image_file(),
        )
        cls.test_image_2 = cls.image_model.objects.create(
            title="Test image 2",
            file=get_test_image_file(),
        )
        cls.test_image_3 = cls.image_model.objects.create(
            title="Test image 3",
            file=get_test_image_file(),
        )
        cls.test_document_1 = cls.document_model.objects.create(
            title="Test document 1",
            file=get_test_document_file(),
        )
        cls.test_document_2 = cls.document_model.objects.create(
            title="Test document 2",
            file=get_test_document_file(),
        )

        cls.event_page = EventPage(
            title="Event page",
            slug="event-page",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            feed_image=cls.test_image_1,
        )
        cls.event_page.carousel_items = [
            EventPageCarouselItem(
                caption="hello image 1", image=cls.test_image_1, sort_order=1
            ),
            EventPageCarouselItem(
                caption="hi image 2", image=cls.test_image_2, sort_order=2
            ),
            EventPageCarouselItem(
                caption="it's image 1 again", image=cls.test_image_1, sort_order=3
            ),
            EventPageCarouselItem(
                caption="now a doc", link_document=cls.test_document_2, sort_order=4
            ),
        ]
        cls.root_page = Page.objects.get(id=2)

        with cls.captureOnCommitCallbacks(execute=True):
            cls.root_page.add_child(instance=cls.event_page)
            cls.event_page.save()

        cls.carousel_items = list(cls.event_page.carousel_items.order_by("sort_order"))

    def test_get_references_to_in_bulk_with_empty_queryset_or_list(self):
        with self.assertNumQueries(0):
            refs = ReferenceIndex.get_references_to_in_bulk(
                get_image_model().objects.none()
            )
            self.assertIsInstance(refs, models.QuerySet)
            self.assertEqual(len(refs), 0)

        with self.assertNumQueries(0):
            refs = ReferenceIndex.get_references_to_in_bulk([])
            self.assertIsInstance(refs, models.QuerySet)
            self.assertEqual(len(refs), 0)

    def test_get_references_to_in_bulk_with_queryset(self):
        with self.assertNumQueries(1):
            refs = ReferenceIndex.get_references_to_in_bulk(
                get_image_model().objects.filter(
                    pk__in=[
                        self.test_image_1.pk,
                        self.test_image_2.pk,
                        self.test_image_3.pk,
                    ]
                )
            )
            self.assertIsInstance(refs, models.QuerySet)
            self.assertEqual(len(refs), 4)

        simplified_refs = {
            (
                ref.to_content_type_id,
                ref.to_object_id,
                ref.base_content_type_id,
                ref.object_id,
                ref.content_path,
            )
            for ref in refs
        }
        page_ct = ContentType.objects.get_for_model(Page)
        image_ct = ContentType.objects.get_for_model(self.image_model)
        page_id = str(self.event_page.pk)
        self.assertEqual(
            simplified_refs,
            {
                (
                    image_ct.pk,
                    str(self.test_image_1.pk),
                    page_ct.pk,
                    page_id,
                    f"carousel_items.{self.carousel_items[0].pk}.image",
                ),
                (
                    image_ct.pk,
                    str(self.test_image_1.pk),
                    page_ct.pk,
                    page_id,
                    f"carousel_items.{self.carousel_items[2].pk}.image",
                ),
                (
                    image_ct.pk,
                    str(self.test_image_1.pk),
                    page_ct.pk,
                    page_id,
                    "feed_image",
                ),
                (
                    image_ct.pk,
                    str(self.test_image_2.pk),
                    page_ct.pk,
                    page_id,
                    f"carousel_items.{self.carousel_items[1].pk}.image",
                ),
            },
        )

    def test_get_references_to_in_bulk_with_list_of_mixed_instances(self):
        with self.assertNumQueries(1):
            refs = ReferenceIndex.get_references_to_in_bulk(
                [
                    self.test_image_1,
                    self.test_image_2,
                    self.test_document_1,
                    self.test_document_2,
                ]
            )
            self.assertIsInstance(refs, models.QuerySet)
            self.assertEqual(len(refs), 5)

        simplified_refs = {
            (
                ref.to_content_type_id,
                ref.to_object_id,
                ref.base_content_type_id,
                ref.object_id,
                ref.content_path,
            )
            for ref in refs
        }
        page_ct = ContentType.objects.get_for_model(Page)
        image_ct = ContentType.objects.get_for_model(self.image_model)
        document_ct = ContentType.objects.get_for_model(self.document_model)
        page_id = str(self.event_page.pk)
        self.assertEqual(
            simplified_refs,
            {
                (
                    image_ct.pk,
                    str(self.test_image_1.pk),
                    page_ct.pk,
                    page_id,
                    f"carousel_items.{self.carousel_items[0].pk}.image",
                ),
                (
                    image_ct.pk,
                    str(self.test_image_1.pk),
                    page_ct.pk,
                    page_id,
                    f"carousel_items.{self.carousel_items[2].pk}.image",
                ),
                (
                    image_ct.pk,
                    str(self.test_image_1.pk),
                    page_ct.pk,
                    page_id,
                    "feed_image",
                ),
                (
                    image_ct.pk,
                    str(self.test_image_2.pk),
                    page_ct.pk,
                    page_id,
                    f"carousel_items.{self.carousel_items[1].pk}.image",
                ),
                (
                    document_ct.pk,
                    str(self.test_document_2.pk),
                    page_ct.pk,
                    page_id,
                    f"carousel_items.{self.carousel_items[3].pk}.link_document",
                ),
            },
        )

    def test_get_grouped_references_to_in_bulk_with_empty_queryset_or_list(self):
        with self.assertNumQueries(0):
            refs = ReferenceIndex.get_grouped_references_to_in_bulk(
                get_image_model().objects.none()
            )
            self.assertIsInstance(refs, dict)
            self.assertEqual(len(refs), 0)

        with self.assertNumQueries(0):
            refs = ReferenceIndex.get_grouped_references_to_in_bulk([])
            self.assertIsInstance(refs, dict)
            self.assertEqual(len(refs), 0)

    def test_get_grouped_references_to_in_bulk_with_queryset(self):
        # Two queries: one to get the references, one to evaluate the images so
        # that we can map each image to its references
        with self.assertNumQueries(2):
            refs = ReferenceIndex.get_grouped_references_to_in_bulk(
                get_image_model().objects.filter(
                    pk__in=[
                        self.test_image_1.pk,
                        self.test_image_2.pk,
                        self.test_image_3.pk,
                    ]
                )
            )
            self.assertIsInstance(refs, dict)
            self.assertEqual(len(refs), 3)

        expected_refs = {
            self.test_image_1: [
                (
                    self.event_page.page_ptr,
                    {
                        f"carousel_items.{self.carousel_items[0].pk}.image",
                        f"carousel_items.{self.carousel_items[2].pk}.image",
                        "feed_image",
                    },
                )
            ],
            self.test_image_2: [
                (
                    self.event_page.page_ptr,
                    {f"carousel_items.{self.carousel_items[1].pk}.image"},
                )
            ],
            self.test_image_3: [],
        }
        self.assertEqual(
            {
                item: [
                    (ref_group[0], {ref.content_path for ref in ref_group[1]})
                    for ref_group in ref_groups
                ]
                for item, ref_groups in refs.items()
            },
            expected_refs,
        )

    def test_get_grouped_references_to_in_bulk_with_list_of_mixed_instances(self):
        # We only need one query to get the references, as the images and
        # documents are already loaded in memory.
        with self.assertNumQueries(1):
            refs = ReferenceIndex.get_grouped_references_to_in_bulk(
                [
                    self.test_image_1,
                    self.test_image_2,
                    self.test_document_1,
                    self.test_document_2,
                ]
            )
            self.assertIsInstance(refs, dict)
            self.assertEqual(len(refs), 4)

        expected_refs = {
            self.test_image_1: [
                (
                    self.event_page.page_ptr,
                    {
                        f"carousel_items.{self.carousel_items[0].pk}.image",
                        f"carousel_items.{self.carousel_items[2].pk}.image",
                        "feed_image",
                    },
                )
            ],
            self.test_image_2: [
                (
                    self.event_page.page_ptr,
                    {f"carousel_items.{self.carousel_items[1].pk}.image"},
                )
            ],
            self.test_document_1: [],
            self.test_document_2: [
                (
                    self.event_page.page_ptr,
                    {f"carousel_items.{self.carousel_items[3].pk}.link_document"},
                )
            ],
        }

        self.assertEqual(
            {
                item: [
                    (ref_group[0], {ref.content_path for ref in ref_group[1]})
                    for ref_group in ref_groups
                ]
                for item, ref_groups in refs.items()
            },
            expected_refs,
        )
