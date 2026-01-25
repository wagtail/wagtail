"""
Preview Files Handler for Wagtail
Handles request.FILES during page preview rendering.
This module provides temporary storage and retrieval of uploaded files during preview sessions.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.http import QueryDict
from django.utils.crypto import get_random_string
from django.utils import timezone


class PreviewFilesHandler:
    """
    Handler for managing uploaded files during Wagtail page preview.
    Stores files temporarily in session and makes them accessible during preview rendering.
    """
    
    # Session key for storing file metadata
    SESSION_KEY_PREFIX = '_wagtail_preview_files_'
    
    # Default storage path for temporary preview files
    PREVIEW_STORAGE_PATH = 'preview_temp/'
    
    # Maximum age for preview files (hours)
    MAX_FILE_AGE_HOURS = 24
    
    @classmethod
    def get_session_key(cls, page_id=None):
        """Get the session key for storing preview files metadata."""
        if page_id:
            return f"{cls.SESSION_KEY_PREFIX}{page_id}"
        return cls.SESSION_KEY_PREFIX
    
    @classmethod
    def save_preview_files(cls, request, page_id=None):
        """
        Save uploaded files from request.FILES to temporary storage.
        
        Args:
            request: HttpRequest object containing FILES
            page_id: Optional page ID for scoping preview files
        
        Returns:
            List of saved file metadata
        """
        if not request.FILES:
            return []
        
        saved_files = []
        session_key = cls.get_session_key(page_id)
        
        # Get existing files from session or initialize empty list
        existing_files = request.session.get(session_key, [])
        
        for field_name, uploaded_file in request.FILES.items():
            # Generate unique filename to avoid collisions
            original_filename = uploaded_file.name
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Create storage path
            storage_path = os.path.join(cls.PREVIEW_STORAGE_PATH, unique_filename)
            
            # Save file to storage
            if isinstance(uploaded_file, InMemoryUploadedFile):
                # Handle in-memory files
                file_content = uploaded_file.read()
                saved_name = default_storage.save(storage_path, ContentFile(file_content))
            else:
                # Handle other file types
                saved_name = default_storage.save(storage_path, uploaded_file)
            
            # Create metadata
            file_metadata = {
                'id': uuid.uuid4().hex,
                'field_name': field_name,
                'original_filename': original_filename,
                'storage_path': saved_name,
                'content_type': uploaded_file.content_type,
                'size': uploaded_file.size,
                'uploaded_at': timezone.now().isoformat(),
                'session_key': request.session.session_key,
            }
            
            saved_files.append(file_metadata)
        
        # Update session with combined file list
        all_files = existing_files + saved_files
        request.session[session_key] = all_files
        request.session.modified = True
        
        return saved_files
    
    @classmethod
    def get_preview_files(cls, request, page_id=None):
        """
        Retrieve preview files and reconstruct request.FILES structure.
        
        Args:
            request: HttpRequest object
            page_id: Optional page ID for scoping preview files
        
        Returns:
            dict: {field_name: UploadedFile} mapping
        """
        session_key = cls.get_session_key(page_id)
        if session_key not in request.session:
            return {}
        
        files_metadata = request.session.get(session_key, [])
        files_dict = {}
        
        for meta in files_metadata:
            try:
                # Skip files from other sessions (safety check)
                if meta.get('session_key') != request.session.session_key:
                    continue
                
                # Check if file hasn't expired
                uploaded_at = datetime.fromisoformat(meta['uploaded_at'])
                if timezone.now() - uploaded_at > timedelta(hours=cls.MAX_FILE_AGE_HOURS):
                    continue
                
                # Read file from storage
                file_path = meta['storage_path']
                if default_storage.exists(file_path):
                    with default_storage.open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Reconstruct UploadedFile
                    uploaded_file = SimpleUploadedFile(
                        name=meta['original_filename'],
                        content=file_content,
                        content_type=meta['content_type']
                    )
                    
                    # Handle multiple files for same field
                    if meta['field_name'] in files_dict:
                        if isinstance(files_dict[meta['field_name']], list):
                            files_dict[meta['field_name']].append(uploaded_file)
                        else:
                            files_dict[meta['field_name']] = [files_dict[meta['field_name']], uploaded_file]
                    else:
                        files_dict[meta['field_name']] = uploaded_file
                        
            except Exception as e:
                # Log error but continue with other files
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to load preview file {meta.get('original_filename', 'unknown')}: {e}")
                continue
        
        return files_dict
    
    @classmethod
    def cleanup_page_preview(cls, request, page_id=None):
        """
        Clean up temporary files for a specific page preview.
        
        Args:
            request: HttpRequest object
            page_id: Optional page ID for scoping cleanup
        """
        session_key = cls.get_session_key(page_id)
        if session_key not in request.session:
            return
        
        files_metadata = request.session.get(session_key, [])
        
        # Delete files from storage
        for meta in files_metadata:
            if meta.get('session_key') == request.session.session_key:
                file_path = meta.get('storage_path')
                if file_path and default_storage.exists(file_path):
                    try:
                        default_storage.delete(file_path)
                    except Exception:
                        pass  # Ignore deletion errors
        
        # Remove from session
        if session_key in request.session:
            del request.session[session_key]
            request.session.modified = True
    
    @classmethod
    def cleanup_session_previews(cls, request):
        """
        Clean up all preview files for the current session.
        
        Args:
            request: HttpRequest object
        """
        # Find all preview session keys
        preview_keys = [key for key in request.session.keys() 
                       if key.startswith(cls.SESSION_KEY_PREFIX)]
        
        for session_key in preview_keys:
            files_metadata = request.session.get(session_key, [])
            
            # Filter files for current session
            session_files = [m for m in files_metadata 
                           if m.get('session_key') == request.session.session_key]
            
            # Delete files from storage
            for meta in session_files:
                file_path = meta.get('storage_path')
                if file_path and default_storage.exists(file_path):
                    try:
                        default_storage.delete(file_path)
                    except Exception:
                        pass
            
            # Remove session files belonging to this session
            other_files = [m for m in files_metadata 
                         if m.get('session_key') != request.session.session_key]
            
            if other_files:
                request.session[session_key] = other_files
            else:
                del request.session[session_key]
            
            request.session.modified = True
    
    @classmethod
    def cleanup_all_expired_previews(cls):
        """
        Clean up all expired preview files from storage and sessions.
        This should be called periodically via cron job or task scheduler.
        """
        import django
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        django.setup()
        
        # Get all preview files from storage
        try:
            # List files in preview storage path
            if default_storage.exists(cls.PREVIEW_STORAGE_PATH):
                file_list = default_storage.listdir(cls.PREVIEW_STORAGE_PATH)[1]
                
                for filename in file_list:
                    file_path = os.path.join(cls.PREVIEW_STORAGE_PATH, filename)
                    file_stat = default_storage.get_modified_time(file_path)
                    
                    # Check if file is older than MAX_FILE_AGE_HOURS
                    if timezone.now() - file_stat > timedelta(hours=cls.MAX_FILE_AGE_HOURS):
                        try:
                            default_storage.delete(file_path)
                        except Exception:
                            pass
        except Exception:
            pass
        
        # Clean up session data (optional - more complex)
        # This would require scanning all sessions, which might be heavy


# Monkey-patch functions to integrate with Wagtail preview system
def patch_wagtail_previews():
    """
    Patch Wagtail's preview functions to handle request.FILES.
    This function should be called in your Django app's ready() method.
    """
    try:
        from wagtail.admin.views.preview import PreviewOnEdit, PreviewOnCreate
        from wagtail.views import serve_preview
        
        # Store original methods
        original_preview_on_edit_post = PreviewOnEdit.post
        original_preview_on_create_post = PreviewOnCreate.post
        original_serve_preview = serve_preview
        
        def patched_preview_on_edit_post(self, request, page_id):
            """Patched PreviewOnEdit.post to handle files"""
            # Save preview files
            PreviewFilesHandler.save_preview_files(request, page_id)
            # Call original method
            return original_preview_on_edit_post(self, request, page_id)
        
        def patched_preview_on_create_post(self, request, page_type_id):
            """Patched PreviewOnCreate.post to handle files"""
            # Save preview files
            PreviewFilesHandler.save_preview_files(request)
            # Call original method
            return original_preview_on_create_post(self, request, page_type_id)
        
        def patched_serve_preview(request, page, mode):
            """Patched serve_preview to handle files"""
            # Get preview data from session
            from django.http import QueryDict
            preview_data = request.session.get('preview_data', {})
            
            # Get preview files
            preview_files = PreviewFilesHandler.get_preview_files(request)
            
            # Create mutable QueryDict from preview data
            mutable_data = QueryDict('', mutable=True)
            mutable_data.update(preview_data)
            
            # Get form class
            form_class = page.get_edit_handler().get_form(
                instance=page, for_user=request.user
            )
            
            # Create form instance with both data and files
            form = form_class(mutable_data, preview_files, instance=page)
            
            if form.is_valid():
                page = form.save(commit=False)
            
            # Call original serve_preview function with updated page
            return original_serve_preview(request, page, mode)
        
        # Apply patches
        PreviewOnEdit.post = patched_preview_on_edit_post
        PreviewOnCreate.post = patched_preview_on_create_post
        
        # Note: serve_preview patching requires more careful handling
        # since it's a function, not a method
        import wagtail.views
        wagtail.views.serve_preview = patched_serve_preview
        
        print("Wagtail previews patched successfully to handle request.FILES")
        
    except ImportError as e:
        print(f"Failed to patch Wagtail previews: {e}")


# Middleware for automatic cleanup
class PreviewFilesCleanupMiddleware:
    """
    Middleware to clean up preview files when user navigates away from preview.
    Add this to your MIDDLEWARE setting.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Clean up preview files if we're leaving preview mode
        if hasattr(request, 'is_preview') and request.is_preview:
            referer = request.META.get('HTTP_REFERER', '')
            current_path = request.path
            
            # If not in preview-related paths, clean up
            preview_paths = ['/admin/pages/', '/draft/', '/preview/']
            if not any(p in current_path for p in preview_paths):
                PreviewFilesHandler.cleanup_session_previews(request)
        
        return response


# Alternative: Decorator-based approach
def with_preview_files(view_func):
    """
    Decorator to add preview files handling to any view.
    Usage: @with_preview_files
    """
    def wrapped_view(request, *args, **kwargs):
        # Check if this is a preview POST request
        if request.method == 'POST' and 'preview' in request.path:
            # Save files if present
            if request.FILES:
                page_id = kwargs.get('page_id')
                PreviewFilesHandler.save_preview_files(request, page_id)
        
        response = view_func(request, *args, **kwargs)
        return response
    
    return wrapped_view


# Example usage in settings.py:
"""
# Add to MIDDLEWARE
MIDDLEWARE = [
    # ...
    'your_app.wagtail_preview_files_handler.PreviewFilesCleanupMiddleware',
    # ...
]

# Add to your AppConfig.ready() method:
from .wagtail_preview_files_handler import patch_wagtail_previews
patch_wagtail_previews()
"""

# Quick test function
def test_preview_files():
    """Test the preview files handler"""
    from django.test import RequestFactory
    from django.contrib.sessions.middleware import SessionMiddleware
    
    # Create mock request
    factory = RequestFactory()
    request = factory.post('/preview/')
    
    # Add session
    middleware = SessionMiddleware(lambda req: None)
    middleware.process_request(request)
    request.session.save()
    
    # Test file saving and retrieval
    test_file = SimpleUploadedFile(
        "test.jpg",
        b"fake image content",
        content_type="image/jpeg"
    )
    
    request.FILES = {'image': test_file}
    
    # Save files
    saved = PreviewFilesHandler.save_preview_files(request)
    print(f"Saved {len(saved)} files")
    
    # Retrieve files
    retrieved = PreviewFilesHandler.get_preview_files(request)
    print(f"Retrieved {len(retrieved)} files")
    
    # Cleanup
    PreviewFilesHandler.cleanup_session_previews(request)
    print("Cleanup complete")
    
    return len(saved) == 1 and len(retrieved) == 1


if __name__ == "__main__":
    # Run test if file is executed directly
    print("Testing PreviewFilesHandler...")
    success = test_preview_files()
    print(f"Test {'passed' if success else 'failed'}")
