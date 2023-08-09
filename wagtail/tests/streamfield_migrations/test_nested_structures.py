from django.test import TestCase

from wagtail.blocks.migrations.operations import (
    RemoveStreamChildrenOperation,
    RemoveStructChildrenOperation,
    RenameStreamChildrenOperation,
    RenameStructChildrenOperation,
)
from wagtail.blocks.migrations.utils import apply_changes_to_raw_data
from wagtail.test.streamfield_migrations import factories, models


class FieldStructStreamChildBlockTest(TestCase):
    """Tests involving changes to children of a StreamBlock nested inside a StructBlock

    We use `nestedstruct.simplestream` blocks here.
    """

    def setUp(self):
        raw_data = factories.SampleModelFactory(
            content__0__char1__value="Char Block 1",
            content__1="nestedstruct",
            content__1__nestedstruct__list1__0__value="a",
            content__1__nestedstruct__stream1__0__char1__value="Char Block 1",
            content__1__nestedstruct__stream1__1__char2__value="Char Block 2",
            content__1__nestedstruct__stream1__2__char1__value="Char Block 1",
            content__2="nestedstruct",
            content__2__nestedstruct__list1__0__value="a",
            content__2__nestedstruct__stream1__0__char1__value="Char Block 1",
            content__3="simplestream",
            content__3__simplestream__0__char1__value="Char Block 1",
            content__3__simplestream__1__char2__value="Char Block 2",
        ).content.raw_data
        self.raw_data = raw_data

    def test_blocks_and_data_not_operated_on_intact(self):
        """Test whether other blocks and data not passed to an operation are intact.

        We are checking whether the parts of the data which are not passed to an operation are
        intact. Since the recursion process depends just on the block path and block structure,
        this check is independent of the operation used. We will use a rename operation for now.
        """

        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstruct.stream1",
            operation=RenameStreamChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(altered_raw_data[0], self.raw_data[0])
        self.assertEqual(altered_raw_data[3], self.raw_data[3])

        self.assertEqual(altered_raw_data[1]["id"], self.raw_data[1]["id"])
        self.assertEqual(altered_raw_data[2]["id"], self.raw_data[2]["id"])
        self.assertEqual(altered_raw_data[1]["type"], self.raw_data[1]["type"])
        self.assertEqual(altered_raw_data[2]["type"], self.raw_data[2]["type"])

        for key in self.raw_data[1]["value"].keys():
            self.assertIn(key, altered_raw_data[1]["value"])
        for key in self.raw_data[1]["value"].keys():
            self.assertIn(key, altered_raw_data[2]["value"])

        self.assertEqual(
            altered_raw_data[1]["value"]["char1"], self.raw_data[1]["value"]["char1"]
        )
        self.assertEqual(
            altered_raw_data[2]["value"]["char1"], self.raw_data[2]["value"]["char1"]
        )
        self.assertEqual(
            altered_raw_data[1]["value"]["struct1"],
            self.raw_data[1]["value"]["struct1"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"]["struct1"],
            self.raw_data[2]["value"]["struct1"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"]["list1"], self.raw_data[1]["value"]["list1"]
        )
        self.assertEqual(
            altered_raw_data[2]["value"]["list1"], self.raw_data[2]["value"]["list1"]
        )

    def test_rename(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstruct.stream1",
            operation=RenameStreamChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(altered_raw_data[1]["value"]["stream1"][0]["type"], "renamed1")
        self.assertEqual(altered_raw_data[1]["value"]["stream1"][2]["type"], "renamed1")
        self.assertEqual(altered_raw_data[2]["value"]["stream1"][0]["type"], "renamed1")

        self.assertEqual(
            altered_raw_data[1]["value"]["stream1"][0]["id"],
            self.raw_data[1]["value"]["stream1"][0]["id"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"]["stream1"][2]["id"],
            self.raw_data[1]["value"]["stream1"][2]["id"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"]["stream1"][0]["id"],
            self.raw_data[2]["value"]["stream1"][0]["id"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"]["stream1"][0]["value"],
            self.raw_data[1]["value"]["stream1"][0]["value"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"]["stream1"][2]["value"],
            self.raw_data[1]["value"]["stream1"][2]["value"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"]["stream1"][0]["value"],
            self.raw_data[2]["value"]["stream1"][0]["value"],
        )

        self.assertEqual(
            altered_raw_data[1]["value"]["stream1"][1],
            self.raw_data[1]["value"]["stream1"][1],
        )

    def test_remove(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstruct.stream1",
            operation=RemoveStreamChildrenOperation(name="char1"),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(len(altered_raw_data[1]["value"]["stream1"]), 1)
        self.assertEqual(len(altered_raw_data[2]["value"]["stream1"]), 0)

        self.assertEqual(
            altered_raw_data[1]["value"]["stream1"][0],
            self.raw_data[1]["value"]["stream1"][1],
        )


class FieldStructStructChildBlockTest(TestCase):
    """Tests involving changes to a children of a StructBlock nested inside a StructBlock

    We use `nestedstruct.simplestruct` blocks here
    """

    def setUp(self):
        raw_data = factories.SampleModelFactory(
            content__0__char1__value="Char Block 1",
            content__1="nestedstruct",
            content__1__nestedstruct__list1__0__value="a",
            content__2="nestedstruct",
            content__2__nestedstruct__list1__0__value="a",
            content__3="simplestruct",
        ).content.raw_data
        self.raw_data = raw_data

    def test_blocks_and_data_not_operated_on_intact(self):
        """Test whether other blocks and data not passed to an operation are intact.

        We are checking whether the parts of the data which are not passed to an operation are
        intact. Since the recursion process depends just on the block path and block structure,
        this check is independent of the operation used. We will use a rename operation for now.
        """

        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstruct.struct1",
            operation=RenameStructChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(altered_raw_data[0], self.raw_data[0])
        self.assertEqual(altered_raw_data[3], self.raw_data[3])

        self.assertEqual(altered_raw_data[1]["type"], self.raw_data[1]["type"])
        self.assertEqual(altered_raw_data[2]["type"], self.raw_data[2]["type"])
        self.assertEqual(altered_raw_data[1]["id"], self.raw_data[1]["id"])
        self.assertEqual(altered_raw_data[2]["id"], self.raw_data[2]["id"])

        for key in self.raw_data[1]["value"].keys():
            self.assertIn(key, altered_raw_data[1]["value"])
        for key in self.raw_data[1]["value"].keys():
            self.assertIn(key, altered_raw_data[2]["value"])

        self.assertEqual(
            altered_raw_data[1]["value"]["char1"], self.raw_data[1]["value"]["char1"]
        )
        self.assertEqual(
            altered_raw_data[2]["value"]["char1"], self.raw_data[2]["value"]["char1"]
        )
        self.assertEqual(
            altered_raw_data[1]["value"]["stream1"],
            self.raw_data[1]["value"]["stream1"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"]["stream1"],
            self.raw_data[2]["value"]["stream1"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"]["list1"], self.raw_data[1]["value"]["list1"]
        )
        self.assertEqual(
            altered_raw_data[2]["value"]["list1"], self.raw_data[2]["value"]["list1"]
        )

    def test_rename(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstruct.struct1",
            operation=RenameStructChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertNotIn("char1", altered_raw_data[1]["value"]["struct1"])
        self.assertNotIn("char1", altered_raw_data[2]["value"]["struct1"])
        self.assertIn("renamed1", altered_raw_data[2]["value"]["struct1"])
        self.assertIn("renamed1", altered_raw_data[2]["value"]["struct1"])

        self.assertIn("char2", altered_raw_data[1]["value"]["struct1"])
        self.assertIn("char2", altered_raw_data[2]["value"]["struct1"])

    def test_remove(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstruct.struct1",
            operation=RemoveStructChildrenOperation(name="char1"),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(len(altered_raw_data[1]["value"]["struct1"]), 1)
        self.assertEqual(len(altered_raw_data[2]["value"]["struct1"]), 1)

        self.assertNotIn("char1", altered_raw_data[1]["value"]["struct1"])
        self.assertNotIn("char1", altered_raw_data[2]["value"]["struct1"])

        self.assertIn("char2", altered_raw_data[1]["value"]["struct1"])
        self.assertIn("char2", altered_raw_data[2]["value"]["struct1"])


class FieldStreamStreamChildBlockTest(TestCase):
    """Tests involving changes to children of a StreamBlock nested inside a StreamBlock.

    We use `nestedstream.stream1` blocks here.
    """

    def setUp(self):
        raw_data = factories.SampleModelFactory(
            content__0__char1__value="Char Block 1",
            content__1="nestedstream",
            content__1__nestedstream__0__char1__value="Char Block 1",
            content__1__nestedstream__1="stream1",
            content__1__nestedstream__1__stream1__0__char1__value="Char Block 1",
            content__1__nestedstream__1__stream1__1__char2__value="Char Block 2",
            content__1__nestedstream__1__stream1__2__char1__value="Char Block 1",
            content__1__nestedstream__2="stream1",
            content__1__nestedstream__2__stream1__0__char1__value="Char Block 1",
            content__2="nestedstream",
            content__2__nestedstream__0="stream1",
            content__2__nestedstream__0__stream1__0__char1__value="Char Block 1",
            content__3="simplestream",
            content__3__simplestream__0__char1__value="Char Block 1",
        ).content.raw_data
        self.raw_data = raw_data

    def test_blocks_and_data_not_operated_on_intact(self):
        """Test whether other blocks and data not passed to an operation are intact.

        We are checking whether the parts of the data which are not passed to an operation are
        intact. Since the recursion process depends just on the block path and block structure,
        this check is independent of the operation used. We will use a rename operation for now.
        """

        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstream.stream1",
            operation=RenameStreamChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(altered_raw_data[0], self.raw_data[0])
        self.assertEqual(altered_raw_data[3], self.raw_data[3])

        self.assertEqual(altered_raw_data[1]["type"], self.raw_data[1]["type"])
        self.assertEqual(altered_raw_data[2]["type"], self.raw_data[2]["type"])
        self.assertEqual(altered_raw_data[1]["id"], self.raw_data[1]["id"])
        self.assertEqual(altered_raw_data[2]["id"], self.raw_data[2]["id"])

        self.assertEqual(altered_raw_data[1]["value"][0], self.raw_data[1]["value"][0])

        self.assertEqual(
            altered_raw_data[1]["value"][1]["type"],
            self.raw_data[1]["value"][1]["type"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["type"],
            self.raw_data[1]["value"][2]["type"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["type"],
            self.raw_data[2]["value"][0]["type"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["id"],
            self.raw_data[1]["value"][1]["id"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["id"],
            self.raw_data[1]["value"][2]["id"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["id"],
            self.raw_data[2]["value"][0]["id"],
        )

    def test_rename(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstream.stream1",
            operation=RenameStreamChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][0]["type"], "renamed1"
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][2]["type"], "renamed1"
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["value"][0]["type"], "renamed1"
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"][0]["type"], "renamed1"
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][0]["id"],
            self.raw_data[1]["value"][1]["value"][0]["id"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][2]["id"],
            self.raw_data[1]["value"][1]["value"][2]["id"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["value"][0]["id"],
            self.raw_data[1]["value"][2]["value"][0]["id"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"][0]["id"],
            self.raw_data[2]["value"][0]["value"][0]["id"],
        )

        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][1],
            self.raw_data[1]["value"][1]["value"][1],
        )

    def test_remove(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstream.stream1",
            operation=RemoveStreamChildrenOperation(name="char1"),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(len(altered_raw_data[1]["value"][1]["value"]), 1)
        self.assertEqual(len(altered_raw_data[1]["value"][2]["value"]), 0)
        self.assertEqual(len(altered_raw_data[2]["value"][0]["value"]), 0)

        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][0],
            self.raw_data[1]["value"][1]["value"][1],
        )


class FieldStreamStructChildBlockTest(TestCase):
    """Tests involving changes to children of a StructBlock nested inside a StreamBlock.

    We use `nestedstream.simplestruct` blocks here.
    """

    def setUp(self):
        raw_data = factories.SampleModelFactory(
            content__0__char1__value="Char Block 1",
            content__1="nestedstream",
            content__1__nestedstream__0__char1="Char Block 1",
            content__1__nestedstream__1="struct1",
            content__1__nestedstream__2="struct1",
            content__2="nestedstream",
            content__2__nestedstream__0="struct1",
            content__3="simplestream",
            content__3__simplestream__0__char1__value="Char Block 1",
        ).content.raw_data
        self.raw_data = raw_data

    def test_blocks_and_data_not_operated_on_intact(self):
        """Test whether other blocks and data not passed to an operation are intact.

        We are checking whether the parts of the data which are not passed to an operation are
        intact. Since the recursion process depends just on the block path and block structure,
        this check is independent of the operation used. We will use a rename operation for now.
        """

        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstream.struct1",
            operation=RenameStructChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(altered_raw_data[0], self.raw_data[0])
        self.assertEqual(altered_raw_data[3], self.raw_data[3])

        self.assertEqual(altered_raw_data[1]["type"], self.raw_data[1]["type"])
        self.assertEqual(altered_raw_data[2]["type"], self.raw_data[2]["type"])
        self.assertEqual(altered_raw_data[1]["id"], self.raw_data[1]["id"])
        self.assertEqual(altered_raw_data[2]["id"], self.raw_data[2]["id"])

        self.assertEqual(altered_raw_data[1]["value"][0], self.raw_data[1]["value"][0])

        self.assertEqual(
            altered_raw_data[1]["value"][1]["type"],
            self.raw_data[1]["value"][1]["type"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["type"],
            self.raw_data[1]["value"][2]["type"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["type"],
            self.raw_data[2]["value"][0]["type"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["id"],
            self.raw_data[1]["value"][1]["id"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["id"],
            self.raw_data[1]["value"][2]["id"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["id"],
            self.raw_data[2]["value"][0]["id"],
        )

    def test_rename(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstream.struct1",
            operation=RenameStructChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertNotIn("char1", altered_raw_data[1]["value"][1]["value"])
        self.assertNotIn("char1", altered_raw_data[1]["value"][2]["value"])
        self.assertNotIn("char1", altered_raw_data[2]["value"][0]["value"])
        self.assertIn("renamed1", altered_raw_data[1]["value"][1]["value"])
        self.assertIn("renamed1", altered_raw_data[1]["value"][2]["value"])
        self.assertIn("renamed1", altered_raw_data[2]["value"][0]["value"])

        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"]["renamed1"],
            self.raw_data[1]["value"][1]["value"]["char1"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["value"]["renamed1"],
            self.raw_data[1]["value"][2]["value"]["char1"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"]["renamed1"],
            self.raw_data[2]["value"][0]["value"]["char1"],
        )

        self.assertIn("char2", altered_raw_data[1]["value"][1]["value"])
        self.assertIn("char2", altered_raw_data[1]["value"][2]["value"])
        self.assertIn("char2", altered_raw_data[2]["value"][0]["value"])

        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"]["char2"],
            self.raw_data[1]["value"][1]["value"]["char2"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["value"]["char2"],
            self.raw_data[1]["value"][2]["value"]["char2"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"]["char2"],
            self.raw_data[2]["value"][0]["value"]["char2"],
        )

    def test_remove(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedstream.struct1",
            operation=RemoveStructChildrenOperation(name="char1"),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(len(altered_raw_data[1]["value"][1]["value"]), 1)
        self.assertEqual(len(altered_raw_data[1]["value"][2]["value"]), 1)
        self.assertEqual(len(altered_raw_data[2]["value"][0]["value"]), 1)

        self.assertIn("char2", altered_raw_data[1]["value"][1]["value"])
        self.assertIn("char2", altered_raw_data[1]["value"][2]["value"])
        self.assertIn("char2", altered_raw_data[2]["value"][0]["value"])

        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"]["char2"],
            self.raw_data[1]["value"][1]["value"]["char2"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][2]["value"]["char2"],
            self.raw_data[1]["value"][2]["value"]["char2"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"]["char2"],
            self.raw_data[2]["value"][0]["value"]["char2"],
        )


class FieldListStreamChildBlockTest(TestCase):
    """Tests involving changes to children of a StreamBlock nested inside a ListBlock.

    We use `nestedlist_stream.item` blocks here.
    """

    def setUp(self):
        raw_data = factories.SampleModelFactory(
            content__0__char1__value="Char Block 1",
            content__1="nestedlist_stream",
            content__1__nestedlist_stream__0__0__char1__value="Char Block 1",
            content__1__nestedlist_stream__0__1__char2__value="Char Block 2",
            content__1__nestedlist_stream__0__2__char1__value="Char Block 1",
            content__1__nestedlist_stream__1__0__char1__value="Char Block 1",
            content__2="nestedlist_stream",
            content__2__nestedlist_stream__0__0__char1__value="Char Block 1",
            content__3="simplestream",
            content__3__simplestream__0__char1__value="Char Block 1",
            content__3__simplestream__1__char2__value="Char Block 2",
        ).content.raw_data
        self.raw_data = raw_data

    def test_blocks_and_data_not_operated_on_intact(self):
        """Test whether other blocks and data not passed to an operation are intact.

        We are checking whether the parts of the data which are not passed to an operation are
        intact. Since the recursion process depends just on the block path and block structure,
        this check is independent of the operation used. We will use a rename operation for now.
        """

        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedlist_stream.item",
            operation=RenameStreamChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(altered_raw_data[0], self.raw_data[0])
        self.assertEqual(altered_raw_data[3], self.raw_data[3])

        self.assertEqual(altered_raw_data[1]["type"], self.raw_data[1]["type"])
        self.assertEqual(altered_raw_data[2]["type"], self.raw_data[2]["type"])
        self.assertEqual(altered_raw_data[1]["id"], self.raw_data[1]["id"])
        self.assertEqual(altered_raw_data[2]["id"], self.raw_data[2]["id"])

        self.assertEqual(
            altered_raw_data[1]["value"][0]["type"],
            self.raw_data[1]["value"][0]["type"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["type"],
            self.raw_data[1]["value"][1]["type"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["type"],
            self.raw_data[2]["value"][0]["type"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][0]["id"], self.raw_data[1]["value"][0]["id"]
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["id"], self.raw_data[1]["value"][1]["id"]
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["id"], self.raw_data[2]["value"][0]["id"]
        )

    def test_rename(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedlist_stream.item",
            operation=RenameStreamChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][0]["type"], "renamed1"
        )
        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][2]["type"], "renamed1"
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][0]["type"], "renamed1"
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"][0]["type"], "renamed1"
        )

        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][0]["id"],
            self.raw_data[1]["value"][0]["value"][0]["id"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][2]["id"],
            self.raw_data[1]["value"][0]["value"][2]["id"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][0]["id"],
            self.raw_data[1]["value"][1]["value"][0]["id"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"][0]["id"],
            self.raw_data[2]["value"][0]["value"][0]["id"],
        )

        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][0]["value"],
            self.raw_data[1]["value"][0]["value"][0]["value"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][2]["value"],
            self.raw_data[1]["value"][0]["value"][2]["value"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"][0]["value"],
            self.raw_data[1]["value"][1]["value"][0]["value"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"][0]["value"],
            self.raw_data[2]["value"][0]["value"][0]["value"],
        )

        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][1],
            self.raw_data[1]["value"][0]["value"][1],
        )

    def test_remove(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedlist_stream.item",
            operation=RemoveStreamChildrenOperation(name="char1"),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(len(altered_raw_data[1]["value"][0]["value"]), 1)
        self.assertEqual(len(altered_raw_data[1]["value"][1]["value"]), 0)
        self.assertEqual(len(altered_raw_data[2]["value"][0]["value"]), 0)

        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"][0],
            self.raw_data[1]["value"][0]["value"][1],
        )


class FieldListStructChildBlockTest(TestCase):
    """Tests involving changes to children of a StructBlock nested inside a ListBlock.

    We use `nestedlist_struct.item` blocks here.
    """

    def setUp(self):
        raw_data = factories.SampleModelFactory(
            content__0__char1__value="Char Block 1",
            content__1__nestedlist_struct__0__char1="Nested List Struct 1",
            content__1__nestedlist_struct__1__char1="Nested List Struct 2",
            content__2__nestedlist_struct__0__char1="Nested List Struct 3",
            content__3="simplestruct",
        ).content.raw_data
        self.raw_data = raw_data

    def test_blocks_and_data_not_operated_on_intact(self):
        """Test whether other blocks and data not passed to an operation are intact.

        We are checking whether the parts of the data which are not passed to an operation are
        intact. Since the recursion process depends just on the block path and block structure,
        this check is independent of the operation used. We will use a rename operation for now.
        """

        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedlist_struct.item",
            operation=RenameStructChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertEqual(altered_raw_data[0], self.raw_data[0])
        self.assertEqual(altered_raw_data[3], self.raw_data[3])

        self.assertEqual(altered_raw_data[1]["type"], self.raw_data[1]["type"])
        self.assertEqual(altered_raw_data[2]["type"], self.raw_data[2]["type"])
        self.assertEqual(altered_raw_data[1]["id"], self.raw_data[1]["id"])
        self.assertEqual(altered_raw_data[2]["id"], self.raw_data[2]["id"])

        self.assertEqual(
            altered_raw_data[1]["value"][0]["id"], self.raw_data[1]["value"][0]["id"]
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["id"], self.raw_data[1]["value"][1]["id"]
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["id"], self.raw_data[2]["value"][0]["id"]
        )

    def test_rename(self):
        altered_raw_data = apply_changes_to_raw_data(
            raw_data=self.raw_data,
            block_path_str="nestedlist_struct.item",
            operation=RenameStructChildrenOperation(
                old_name="char1", new_name="renamed1"
            ),
            streamfield=models.SampleModel.content,
        )

        self.assertNotIn("char1", altered_raw_data[1]["value"][0]["value"])
        self.assertNotIn("char1", altered_raw_data[1]["value"][1]["value"])
        self.assertNotIn("char1", altered_raw_data[2]["value"][0]["value"])
        self.assertIn("renamed1", altered_raw_data[1]["value"][0]["value"])
        self.assertIn("renamed1", altered_raw_data[1]["value"][1]["value"])
        self.assertIn("renamed1", altered_raw_data[2]["value"][0]["value"])
        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"]["renamed1"],
            self.raw_data[1]["value"][0]["value"]["char1"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"]["renamed1"],
            self.raw_data[1]["value"][1]["value"]["char1"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"]["renamed1"],
            self.raw_data[2]["value"][0]["value"]["char1"],
        )

        self.assertIn("char2", altered_raw_data[1]["value"][0]["value"])
        self.assertIn("char2", altered_raw_data[1]["value"][1]["value"])
        self.assertIn("char2", altered_raw_data[2]["value"][0]["value"])
        self.assertEqual(
            altered_raw_data[1]["value"][0]["value"]["char2"],
            self.raw_data[1]["value"][0]["value"]["char2"],
        )
        self.assertEqual(
            altered_raw_data[1]["value"][1]["value"]["char2"],
            self.raw_data[1]["value"][1]["value"]["char2"],
        )
        self.assertEqual(
            altered_raw_data[2]["value"][0]["value"]["char2"],
            self.raw_data[2]["value"][0]["value"]["char2"],
        )
