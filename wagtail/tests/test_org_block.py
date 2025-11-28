from django.test import TestCase

from wagtail import blocks


class OrgNodeBlock(blocks.StructBlock):
    org_title = blocks.CharBlock(help_text="Role title")
    person_name = blocks.CharBlock(required=False)
    reports = blocks.ListBlock("OrgNodeBlock", required=False, max_depth=3)

    class Meta:
        icon = "user"


class TreeNodeBlock(blocks.StructBlock):
    value = blocks.CharBlock()
    children = blocks.ListBlock("TreeNodeBlock", required=False, max_depth=5)


class TestSelfReferentialListBlock(TestCase):
    def test_string_reference_resolution(self):
        org_block = OrgNodeBlock()
        reports_field = org_block.child_blocks["reports"]

        self.assertEqual(type(reports_field).__name__, "ListBlock")
        self.assertEqual(reports_field._child_block_ref, "OrgNodeBlock")

        # Verify the child block gets resolved to the correct type
        self.assertTrue(reports_field._resolved)
        self.assertEqual(type(reports_field.child_block).__name__, "OrgNodeBlock")

        # Verify nested structure works
        nested_reports = reports_field.child_block.child_blocks["reports"]
        self.assertEqual(type(nested_reports).__name__, "ListBlock")
        self.assertEqual(nested_reports._child_block_ref, "OrgNodeBlock")

    def test_max_depth_parameter(self):
        tree_block = TreeNodeBlock()
        children_field = tree_block.child_blocks["children"]

        self.assertEqual(children_field.max_depth, 5)

    def test_circular_reference_detection(self):
        org_block = OrgNodeBlock()
        reports_field = org_block.child_blocks["reports"]

        self.assertTrue(hasattr(reports_field, "_resolving_references"))
        self.assertTrue(hasattr(reports_field, "_checking_references"))

        reports_field._resolve_child_block()
        self.assertTrue(reports_field._resolved)
