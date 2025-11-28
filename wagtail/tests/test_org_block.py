import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wagtail.test.settings')
django.setup()

from wagtail import blocks


class OrgNodeBlock(blocks.StructBlock):
    org_title = blocks.CharBlock(help_text="Role title (e.g., 'CEO')")
    person_name = blocks.CharBlock(required=False, help_text="Person's name")
    reports = blocks.ListBlock('OrgNodeBlock', required=False, label="Reports", max_depth=3)
    
    class Meta:
        icon = "user"


if __name__ == "__main__":
    org_block = OrgNodeBlock()
    reports_field = org_block.child_blocks['reports']
    
    print(f"Block: {type(org_block).__name__}")
    print(f"Reports field: {type(reports_field).__name__}")
    print(f"Child block ref: {reports_field._child_block_ref}")
    print(f"Resolved: {reports_field._resolved}")
    
    reports_field._resolve_child_block()
    
    print(f"After resolution: {type(reports_field.child_block).__name__}")
    print(f"Self-referential: {type(reports_field.child_block).__name__ == 'OrgNodeBlock'}")
