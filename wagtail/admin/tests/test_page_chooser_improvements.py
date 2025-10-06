"""
Tests for page chooser improvements (GitHub issue #12927)
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from wagtail.models import Page
from wagtail.admin.views.chooser import BrowseView, can_choose_page
from wagtail.test.utils import WagtailTestUtils


User = get_user_model()


class TestPageModel(Page):
    """Test page model with restricted parent types"""
    parent_page_types = ['wagtailadmin.TestParentPage']
    
    class Meta:
        app_label = 'wagtailadmin'


class TestParentPage(Page):
    """Test parent page model"""
    subpage_types = ['wagtailadmin.TestPageModel']
    
    class Meta:
        app_label = 'wagtailadmin'


class PageChooserImprovementsTest(TestCase, WagtailTestUtils):
    """Test the page chooser improvements for restricted parent types"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.create_superuser('admin', 'admin@example.com', 'password')
        self.root_page = Page.get_first_root_node()
        
        # Create test page structure
        self.parent_page = TestParentPage(title="Test Parent", slug="test-parent")
        self.root_page.add_child(instance=self.parent_page)
        
        self.child_page = TestPageModel(title="Test Child", slug="test-child")
        self.parent_page.add_child(instance=self.child_page)
        
        self.invalid_parent = Page(title="Invalid Parent", slug="invalid-parent")
        self.root_page.add_child(instance=self.invalid_parent)
    
    def test_can_choose_page_with_restricted_types(self):
        """Test that can_choose_page correctly identifies valid parents"""
        # Valid parent should be choosable
        self.assertTrue(
            can_choose_page(
                self.parent_page,
                self.user,
                (TestParentPage,),
                user_perm="move_to",
                target_pages=[self.child_page]
            )
        )
        
        # Invalid parent should not be choosable
        self.assertFalse(
            can_choose_page(
                self.invalid_parent,
                self.user,
                (TestParentPage,),
                user_perm="move_to",
                target_pages=[self.child_page]
            )
        )
    
    def test_filter_object_list_hides_invalid_parents(self):
        """Test that filter_object_list hides invalid parent pages during move operations"""
        request = self.factory.get('/admin/choose-page/', {
            'user_perms': 'move_to',
            'target_pages[]': [str(self.child_page.pk)],
            'page_type': 'wagtailadmin.TestParentPage'
        })
        request.user = self.user
        
        view = BrowseView()
        view.request = request
        view.desired_classes = (TestParentPage,)
        view.parent_page = self.root_page
        
        # Get all children of root
        pages = self.root_page.get_children()
        
        # Filter them using our improved logic
        filtered_pages = view.filter_object_list(pages)
        
        # Should only contain valid parent pages
        page_ids = list(filtered_pages.values_list('pk', flat=True))
        self.assertIn(self.parent_page.pk, page_ids)
        self.assertNotIn(self.invalid_parent.pk, page_ids)
    
    def test_move_operation_context_variables(self):
        """Test that move operations get proper context variables"""
        request = self.factory.get('/admin/choose-page/', {
            'user_perms': 'move_to',
            'target_pages[]': [str(self.child_page.pk)],
            'page_type': 'wagtailadmin.TestParentPage'
        })
        request.user = self.user
        
        view = BrowseView()
        response = view.get(request, parent_page_id=self.root_page.pk)
        
        # Check that context contains move operation variables
        self.assertIn('is_move_operation', response.context_data)
        self.assertIn('page_to_move', response.context_data)
        self.assertTrue(response.context_data['is_move_operation'])
        self.assertEqual(response.context_data['page_to_move'], self.child_page)
