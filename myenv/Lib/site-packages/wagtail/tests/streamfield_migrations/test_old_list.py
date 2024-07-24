from django.test import TestCase

from wagtail.blocks.migrations.operations import (
    ListChildrenToStructBlockOperation,
    RenameStreamChildrenOperation,
    RenameStructChildrenOperation,
)
from wagtail.blocks.migrations.utils import apply_changes_to_raw_data
from wagtail.test.streamfield_migrations import models


class OldListFormatNestedStreamTestCase(TestCase):
    """Tests involving changes to ListBlocks in the old format with StreamBlock children"""

    @classmethod
    def setUpTestData(cls):
        raw_data = [
            {"type": "char1", "id": "0001", "value": "Char Block 1"},
            {
                "type": "nestedlist_stream",
                "id": "0002",
                "value": [
                    [
                        {"type": "char1", "id": "0003", "value": "Char Block 1"},
                        {"type": "char2", "id": "0004", "value": "Char Block 2"},
                        {"type": "char1", "id": "0005", "value": "Char Block 1"},
                    ],
                    [
                        {"type": "char1", "id": "0006", "value": "Char Block 1"},
                    ],
                ],
            },
            {
                "type": "nestedlist_stream",
                "id": "0007",
                "value": [
                    [
                        {"type": "char1", "id": "0008", "value": "Char Block 1"},
                    ]
                ],
            },
        ]
        cls.raw_data = raw_data

    def test_list_converted_to_new_format_in_recursion(self):
        """Test whether all ListBlock children have converted formats during the recursion.

        This tests the changes done in the recursion process only, so the operation used isn't
        important. We will use a rename operation for now.

        Check whether each ListBlock child has attributes id, value, type and type is item.
        Check whether rename operation was done successfully.
        """

        altered_raw_data = apply_changes_to_raw_data(
            self.raw_data,
            "nestedlist_stream.item",
            RenameStreamChildrenOperation(old_name="char1", new_name="renamed1"),
            streamfield=models.SampleModel.content,
        )

        for listitem in altered_raw_data[1]["value"]:
            self.assertIsInstance(listitem, dict)
            self.assertIn("type", listitem)
            self.assertIn("value", listitem)
            self.assertEqual(listitem["type"], "item")

        for listitem in altered_raw_data[2]["value"]:
            self.assertIsInstance(listitem, dict)
            self.assertIn("type", listitem)
            self.assertIn("value", listitem)
            self.assertEqual(listitem["type"], "item")

        # the nested blocks which were renamed
        altered_block_path_indices = [
            (1, 0, 0),
            (1, 0, 2),
            (1, 1, 0),
            (2, 0, 0),
        ]

        for ind0, ind1, ind2 in altered_block_path_indices:
            self.assertEqual(
                altered_raw_data[ind0]["value"][ind1]["value"][ind2]["type"], "renamed1"
            )

            self.assertEqual(
                altered_raw_data[ind0]["value"][ind1]["value"][ind2]["id"],
                self.raw_data[ind0]["value"][ind1][ind2]["id"],
            )

            self.assertEqual(
                altered_raw_data[ind0]["value"][ind1]["value"][ind2]["value"],
                self.raw_data[ind0]["value"][ind1][ind2]["value"],
            )

        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][1],
            self.raw_data[1]["value"][0][1],
        )

    def test_list_converted_to_new_format_in_operation(self):
        """Test whether all ListBlock children have converted formats in an operation using the generator

        We will test this with the ListChildrenToStructBlockOperation.

        Check whether each ListBlock child has attributes id, value, type and type is item.
        Check whether the ListBlock child value is a struct with the previous block as value.
        Check whether the previous values are intact.
        """

        altered_raw_data = apply_changes_to_raw_data(
            self.raw_data,
            "nestedlist_stream",
            ListChildrenToStructBlockOperation(block_name="stream1"),
            streamfield=models.SampleModel.content,
        )

        for ind, listitem in enumerate(altered_raw_data[1]["value"]):
            self.assertIsInstance(listitem, dict)
            self.assertIn("type", listitem)
            self.assertIn("value", listitem)
            self.assertEqual(listitem["type"], "item")

            self.assertIsInstance(listitem["value"], dict)
            self.assertEqual(len(listitem["value"]), 1)
            self.assertIn("stream1", listitem["value"])

            self.assertEqual(
                listitem["value"]["stream1"], self.raw_data[1]["value"][ind]
            )

        for ind, listitem in enumerate(altered_raw_data[2]["value"]):
            self.assertIsInstance(listitem, dict)
            self.assertIn("type", listitem)
            self.assertIn("value", listitem)
            self.assertEqual(listitem["type"], "item")

            self.assertIsInstance(listitem["value"], dict)
            self.assertEqual(len(listitem["value"]), 1)
            self.assertIn("stream1", listitem["value"])

            self.assertEqual(
                listitem["value"]["stream1"], self.raw_data[2]["value"][ind]
            )


class OldListFormatNestedStructTestCase(TestCase):
    """Tests involving changes to ListBlocks in the old format with StructBlock children"""

    @classmethod
    def setUpTestData(cls):
        raw_data = [
            {"type": "char1", "id": "0001", "value": "Char Block 1"},
            {
                "type": "nestedlist_struct",
                "id": "0002",
                "value": [
                    {"char1": "Char Block 1", "char2": "Char Block 2"},
                    {"char1": "Char Block 1", "char2": "Char Block 2"},
                ],
            },
            {
                "type": "nestedlist_struct",
                "id": "0007",
                "value": [
                    {"char1": "Char Block 1", "char2": "Char Block 2"},
                ],
            },
        ]
        cls.raw_data = raw_data

    def test_list_converted_to_new_format_in_recursion(self):
        """Test whether all ListBlock children have converted formats during the recursion.

        This tests the changes done in the recursion process only, so the operation used isn't
        important. We will use a rename operation for now.

        Check whether each ListBlock child has attributes id, value, type and type is item.
        Check whether rename operation was done successfully.
        """

        altered_raw_data = apply_changes_to_raw_data(
            self.raw_data,
            "nestedlist_struct.item",
            RenameStructChildrenOperation(old_name="char1", new_name="renamed1"),
            streamfield=models.SampleModel.content,
        )

        for listitem in altered_raw_data[1]["value"]:
            self.assertIsInstance(listitem, dict)
            self.assertIn("type", listitem)
            self.assertIn("value", listitem)
            self.assertEqual(listitem["type"], "item")

        for listitem in altered_raw_data[2]["value"]:
            self.assertIsInstance(listitem, dict)
            self.assertIn("type", listitem)
            self.assertIn("value", listitem)
            self.assertEqual(listitem["type"], "item")

        # The nested blocks which were renamed
        altered_block_indices = [(1, 0), (1, 1), (2, 0)]

        for ind0, ind1 in altered_block_indices:
            self.assertNotIn("char1", altered_raw_data[ind0]["value"][ind1]["value"])
            self.assertIn("renamed1", altered_raw_data[ind0]["value"][ind1]["value"])

            self.assertEqual(
                altered_raw_data[ind0]["value"][ind1]["value"]["renamed1"],
                self.raw_data[ind0]["value"][ind1]["char1"],
            )

            self.assertIn("char2", altered_raw_data[ind0]["value"][ind1]["value"])

            self.assertEqual(
                altered_raw_data[ind0]["value"][ind1]["value"]["char2"],
                self.raw_data[ind0]["value"][ind1]["char2"],
            )

    def test_list_converted_to_new_format_in_operation(self):
        """Test whether all ListBlock children have converted formats in an operation using the generator

        We will test this with the ListChildrenToStructBlockOperation.

        Check whether each ListBlock child has attributes id, value, type and type is item.
        Check whether the ListBlock child value is a struct with the previous block as value.
        Check whether the previous values are intact.
        """

        altered_raw_data = apply_changes_to_raw_data(
            self.raw_data,
            "nestedlist_struct",
            ListChildrenToStructBlockOperation(block_name="struct1"),
            streamfield=models.SampleModel.content,
        )

        for ind, listitem in enumerate(altered_raw_data[1]["value"]):
            self.assertIsInstance(listitem, dict)
            self.assertIn("type", listitem)
            self.assertIn("value", listitem)
            self.assertEqual(listitem["type"], "item")

            self.assertIsInstance(listitem["value"], dict)
            self.assertEqual(len(listitem["value"]), 1)
            self.assertIn("struct1", listitem["value"])

            self.assertEqual(
                listitem["value"]["struct1"], self.raw_data[1]["value"][ind]
            )

        for ind, listitem in enumerate(altered_raw_data[2]["value"]):
            self.assertIsInstance(listitem, dict)
            self.assertIn("type", listitem)
            self.assertIn("value", listitem)
            self.assertEqual(listitem["type"], "item")

            self.assertIsInstance(listitem["value"], dict)
            self.assertEqual(len(listitem["value"]), 1)
            self.assertIn("struct1", listitem["value"])

            self.assertEqual(
                listitem["value"]["struct1"], self.raw_data[2]["value"][ind]
            )
