# Bug Report: Page.save_revision() Missing Race Condition Protection

## Title

**Page.save_revision() Missing expected_revision_created_at Parameter Causes TypeError and Lacks Race Condition Protection for Concurrent Autosave**

## Affected Files

| File | Function/Method | Lines |
|------|-----------------|-------|
| `wagtail/models/pages.py` | `Page.save_revision()` | 943-952 |
| `wagtail/admin/views/pages/edit.py` | `EditView.save_action()` | 628-635 |
| `wagtail/models/revisions.py` | `RevisionMixin.save_revision()` | 381-505 |

## Problem Summary

The Page class completely overrides `save_revision()` from `RevisionMixin` but is missing the `expected_revision_created_at` parameter that the page edit view passes.

### Page.save_revision() signature (pages.py:943-952):
```python
def save_revision(
    self,
    user=None,
    approved_go_live_at=None,
    changed=True,
    log_action=False,
    previous_revision=None,
    clean=True,
    overwrite_revision=None,
):  # NO expected_revision_created_at parameter
```

### Page edit view call (edit.py:628-635):
```python
revision = self.page.save_revision(
    user=self.request.user,
    log_action=True,
    previous_revision=self.previous_revision,
    overwrite_revision=overwrite_revision,
    expected_revision_created_at=expected_revision_created_at,  # PASSED BUT NOT ACCEPTED
    clean=False,
)
```

### RevisionMixin.save_revision() (revisions.py:381-391):
```python
def save_revision(
    self,
    ...
    expected_revision_created_at=None,  # CORRECTLY INCLUDED
):
```

## Runtime Behavior

1. When a page is edited with autosave data (`overwrite_revision_id` in POST), the edit view passes `expected_revision_created_at`
2. `Page.save_revision()` does not accept this keyword argument
3. Python raises: `TypeError: save_revision() got an unexpected keyword argument 'expected_revision_created_at'`

Additionally, `Page.save_revision()` lacks race condition protection:
- **No `SELECT FOR UPDATE`**: RevisionMixin locks the revision row, Page does not
- **No timestamp verification**: RevisionMixin verifies `created_at` hasn't changed, Page does not

## Impact

### Immediate Breakage
- All page editing with autosave enabled fails with TypeError

### Silent Data Loss
Without the protection logic, concurrent editors can silently overwrite each other's changes:
- User A and User B edit the same page
- Both autosave triggers around the same time
- One user's changes are silently lost with no warning

## Who Is Affected
- All content teams using Page editing
- Enterprise deployments with multiple editors
- Agencies managing client content collaboratively

## How To Reproduce

### TypeError
1. Navigate to any page in Wagtail admin
2. Make an edit
3. Wait for autosave to trigger
4. Server returns 500 error with TypeError

### Silent Data Loss (after fixing TypeError)
1. User A opens Page X for editing
2. User B opens same page
3. Both make different edits
4. Both autosave at approximately same time
5. One user's changes are silently overwritten

## Root Cause

1. `Page.save_revision()` reimplements logic from `RevisionMixin` without calling `super()`
2. When `expected_revision_created_at` was added to RevisionMixin, Page wasn't updated
3. Missing `SELECT FOR UPDATE` and timestamp verification in Page's implementation

## Suggested Fix

Add the parameter and protection logic to `Page.save_revision()`:

```python
def save_revision(
    self,
    user=None,
    approved_go_live_at=None,
    changed=True,
    log_action=False,
    previous_revision=None,
    clean=True,
    overwrite_revision=None,
    expected_revision_created_at=None,  # ADD THIS
):
    # ... existing checks ...

    if overwrite_revision:
        # Re-fetch with SELECT FOR UPDATE
        try:
            locked_revision = Revision.objects.select_for_update().get(
                pk=overwrite_revision.pk
            )
        except Revision.DoesNotExist:
            raise PermissionDenied("Cannot overwrite a revision that does not exist.")

        # Verify timestamp hasn't changed
        if expected_revision_created_at is not None:
            actual_created_at = locked_revision.created_at.isoformat()
            if actual_created_at != expected_revision_created_at:
                raise PermissionDenied(
                    "This revision has been modified by another session. "
                    "Please refresh and try again."
                )
        # Continue with existing logic using locked_revision
```

## Expected Outcome After Fix

1. Page editing with autosave functions correctly
2. Concurrent editors receive clear error messages on conflicts
3. Pages and snippets have consistent autosave behavior
4. Database-level protection via SELECT FOR UPDATE
