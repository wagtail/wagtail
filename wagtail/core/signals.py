from django.dispatch import Signal


# Page signals

# provides args: instance, revision
page_published = Signal()

# provides args: instance
page_unpublished = Signal()

# provides args: instance, parent_page_before, parent_page_after, url_path_before, url_path_after
pre_page_move = Signal()

# provides args: instance, parent_page_before, parent_page_after, url_path_before, url_path_after
post_page_move = Signal()


# Workflow signals

# provides args: instance, user
workflow_approved = Signal()

# provides args: instance, user
workflow_rejected = Signal()

# provides args: instance, user
workflow_cancelled = Signal()

# provides args: instance, user
workflow_submitted = Signal()


# Workflow task signals

# provides args: instance, user
task_approved = Signal()

# provides args: instance, user
task_rejected = Signal()

# provides args: instance, user
task_submitted = Signal()

# provides args: instance, user
task_cancelled = Signal()


# Locale signals

# Like pre_delete, but sent on deletion before on_delete validation is applied.
# Currently only sent by the Locale model.
# Required as a workaround for https://code.djangoproject.com/ticket/6870
# provides args: sender, instance
pre_validate_delete = Signal()
