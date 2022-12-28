from wagtail.project_template.project_name.settings.base import *
from django.core.checks import Warning,register

@register()
def example_check(app_configs,**kwargs):
    errors = []
    # ... your check logic here
    if DEFAULT_FILE_STORAGE == "storages.backends.s3boto3.S3Boto3Storage" and AWS_S3_FILE_OVERWRITE == True:

        errors.append(
            Warning(
                'Note that the django-storages Amazon S3 backends\n'
                '(storages.backends.s3boto.S3BotoStorage and\n'
                'storages.backends.s3boto3.S3Boto3Storage)\n'
                'do not correctly handle duplicate filenames in their default configuration.\n'
                'When using these backends, AWS_S3_FILE_OVERWRITE must be set to False.\n',
                
                
            )
        )
    return errors
