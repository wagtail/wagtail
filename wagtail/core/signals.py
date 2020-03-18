from django.dispatch import Signal

page_published = Signal(providing_args=['instance', 'revision'])
page_unpublished = Signal(providing_args=['instance'])

workflow_approved = Signal(providing_args=['instance', 'user'])
workflow_rejected = Signal(providing_args=['instance', 'user'])
workflow_cancelled = Signal(providing_args=['instance', 'user'])
workflow_submitted = Signal(providing_args=['instance', 'user'])

task_approved = Signal(providing_args=['instance', 'user'])
task_rejected = Signal(providing_args=['instance', 'user'])
task_submitted = Signal(providing_args=['instance', 'user'])
task_cancelled = Signal(providing_args=['instance' 'user'])
