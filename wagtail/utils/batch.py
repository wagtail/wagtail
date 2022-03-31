from typing import Any, Dict, Iterable, Union

from django.db.models import Model
from django.db.models.base import ModelBase


class BatchProcessor:
    """
    A class to help with processing of an unknown (and potentially very
    high) number of objects.

    Just set ``max_size`` to the maximum number of instances you want
    to be held in memory at any one time, and batches will be sent to the
    ``process()`` method as that number is reached, without you having to
    invoke ``process()`` regularly yourself. Just remember to invoke
    ``process()`` when you're done adding items, otherwise the final batch
    of objects will not be processed.
    """

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.items = []
        self.added_count = 0

    def __len__(self):
        return self.added_count

    def add(self, item: Any) -> None:
        self.items.append(item)
        self.added_count += 1
        if self.max_size and len(self.items) == self.max_size:
            self.process()

    def extend(self, iterable: Iterable[Any]) -> None:
        for item in iterable:
            self.add(item)

    def process(self):
        self.pre_process()
        self._do_processing()
        self.post_process()
        self.items.clear()

    def pre_process(self):
        """
        A hook to allow subclasses to do any pre-processing of the data
        before the ``process()`` method is called.
        """
        pass

    def _do_processing(self):
        """
        To be overridden by subclasses to do whatever it is
        that needs to be done to the items in ``self.items``.
        """
        raise NotImplementedError

    def post_process(self):
        """
        A hook to allow subclasses to do any post-processing
        after the ``process()`` method is called, and before
        ``self.items`` is cleared
        """
        pass


class BatchCreator(BatchProcessor):
    """
    A class to help with bulk creation of an unknown (and potentially very
    high) number of model instances.

    Just set ``max_size`` to the maximum number of instances you want
    to be held in memory at any one time, and batches of objects will
    be created as that number is reached, without you having to invoke
    the ``process()`` method regularly yourself. Just remember to
    invoke ``process()`` when you're done adding items, to ensure
    that the final batch items is saved.

    ``BatchSaver`` is migration-friendly! Just use the ``model``
    keyword argument when initializing to override the hardcoded model
    class with the version from your migration.
    """

    model: ModelBase = None

    def __init__(
        self, max_size: int, *, model: ModelBase = None, ignore_conflicts=False
    ):
        super().__init__(max_size)
        self.ignore_conflicts = ignore_conflicts
        self.created_count = 0
        if model is not None:
            self.model = model

    def initialize_instance(self, kwargs):
        return self.model(**kwargs)

    def add(self, *, instance: Model = None, **kwargs) -> None:
        if instance is None:
            instance = self.initialize_instance(kwargs)
        self.items.append(instance)
        self.added_count += 1
        if self.max_size and len(self.items) == self.max_size:
            self.process()

    def extend(self, iterable: Iterable[Union[Model, Dict[str, Any]]]) -> None:
        for value in iterable:
            if isinstance(value, self.model):
                self.add(instance=value)
            else:
                self.add(**value)

    def _do_processing(self):
        """
        Use bulk_create() to save ``self.items``.
        """
        if not self.items:
            return None
        self.created_count += len(
            self.model.objects.bulk_create(
                self.items, ignore_conflicts=self.ignore_conflicts
            )
        )

    def get_summary(self):
        opts = self.model._meta
        return f"{self.created_count}/{self.added_count} {opts.verbose_name_plural} were created successfully."
