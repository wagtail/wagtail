class PageClassNotFoundError(ImportError):
    """
    Raised when a model class referenced by a page object's ``content_type``
    value cannot be found in the codebase. Usually, this is as a result of
    switching to a different git branch without first running/reverting
    migrations.
    """

    pass
