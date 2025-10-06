# Page Chooser Improvements - GitHub Issue #12927

## Problem Statement

Users found the page chooser confusing when moving pages with restricted parent types (like `WorkPage` that can only be placed under `WorkIndexPage`). The interface showed many grayed-out pages, making it unclear which pages could actually be selected.

## Solution Overview

This implementation addresses the issue by:

1. **Hiding invalid parent pages** instead of showing them grayed out
2. **Starting closer to valid parent pages** for move operations  
3. **Enhancing navigation** with clear folder icons and exploration hints
4. **Providing contextual help** explaining the restrictions

## Changes Made

### Backend Changes (`wagtail/admin/views/chooser.py`)

- **Enhanced `filter_object_list()`**: For move operations, only show pages that can be selected as parents or contain valid parents in their descendants
- **Improved parent page selection**: Smart algorithm to start closer to valid parent pages
- **Added context variables**: `is_move_operation` and `page_to_move` for better template rendering

### Template Changes

#### `wagtailadmin/chooser/_browse_results.html`
- Added contextual help banners explaining the interface
- Enhanced CSS for better navigation styling
- Clear messaging for move operations

#### `wagtailadmin/chooser/tables/page_title_cell.html`
- Improved page display with appropriate icons
- Folder icons for navigation-only pages
- Cleaner interface without disabled page styling

#### `wagtailadmin/chooser/tables/page_navigate_to_children_cell.html`
- Enhanced navigation buttons with folder icons
- Added "Explore" text and child count indicators
- Better visual hierarchy for navigation

## Key Features

### 1. Hide Invalid Pages
- **Before**: Users saw many grayed-out pages they couldn't select
- **After**: Only valid parent pages and navigation folders are shown

### 2. Smart Starting Location
- Automatically starts near existing valid parent pages
- Reduces navigation time for users
- Uses intelligent algorithms to find the best starting point

### 3. Enhanced Navigation
- Clear folder icons with "Explore" buttons
- Child count indicators (e.g., "Explore (3)")
- Yellow highlighting for navigation folders
- Obvious visual cues for tree navigation

### 4. Contextual Help
- Specific messaging: "Moving [page] - it can only be placed under pages of type [type]"
- Clear instructions about using folder icons
- Different messages for move vs. regular operations

## Testing

### Manual Testing
- Created test pages with restricted parent types (`WorkPage` → `WorkIndexPage`)
- Verified that only valid parents are shown during move operations
- Confirmed enhanced navigation works correctly

### Unit Tests
- Added comprehensive tests in `test_page_chooser_improvements.py`
- Tests cover filtering logic, context variables, and edge cases
- Ensures backward compatibility with existing functionality

## Impact

This improvement directly addresses the user confusion described in GitHub issue #12927:

- ✅ **Eliminates grayed-out page confusion**
- ✅ **Provides clear navigation paths**  
- ✅ **Improves overall user experience**
- ✅ **Maintains backward compatibility**

## Files Modified

- `wagtail/admin/views/chooser.py`
- `wagtail/admin/templates/wagtailadmin/chooser/_browse_results.html`
- `wagtail/admin/templates/wagtailadmin/chooser/tables/page_title_cell.html`
- `wagtail/admin/templates/wagtailadmin/chooser/tables/page_navigate_to_children_cell.html`
- `wagtail/admin/tests/test_page_chooser_improvements.py` (new)

## Backward Compatibility

All changes are backward compatible and don't affect existing functionality for users without restricted parent page types.
