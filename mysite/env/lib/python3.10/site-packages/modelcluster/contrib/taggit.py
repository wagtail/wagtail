from __future__ import unicode_literals
from __future__ import absolute_import

from taggit import VERSION as TAGGIT_VERSION
from taggit.managers import TaggableManager, _TaggableManager
from taggit.utils import require_instance_manager

from modelcluster.queryset import FakeQuerySet


if TAGGIT_VERSION < (0, 20, 0):
    raise Exception("modelcluster.contrib.taggit requires django-taggit version 0.20 or above")


class _ClusterTaggableManager(_TaggableManager):
    @require_instance_manager
    def get_tagged_item_manager(self):
        """Return the manager that handles the relation from this instance to the tagged_item class.
        If content_object on the tagged_item class is defined as a ParentalKey, this will be a
        DeferringRelatedManager which allows writing related objects without committing them
        to the database.
        """
        rel_name = self.through._meta.get_field('content_object').remote_field.get_accessor_name()
        return getattr(self.instance, rel_name)

    def get_queryset(self, extra_filters=None):
        if self.instance is not None:
            tagged_item_manager = self.get_tagged_item_manager()

            # If we're already managing tags in memory for this instance,
            # we want to return those uncommitted changes. This shouldn't
            # require a request to the database.
            if tagged_item_manager.is_deferring:
                return FakeQuerySet(
                    self.through.tag_model(),
                    [tagged_item.tag for tagged_item in tagged_item_manager.all()],
                )

            # If we don't have any uncommitted changes for this instance,
            # we'd ideally like to use the default taggit logic. There's one
            # case that we need to handle specially, which is the ability to
            # query tags on an unsaved model instance, for example:
            #
            #   class TaggedPlace(TaggedItemBase):
            #      content_object = ParentalKey(
            #          "Place",
            #          related_name="tagged_items",
            #          on_delete=models.CASCADE,
            #      )
            #
            #   class Place(ClusterableModel):
            #       tags = ClusterTaggableManager(
            #           through=TaggedPlace,
            #           blank=True,
            #       )
            #
            #   instance = Place()
            #   instance.tags.count()
            #
            # Under the hood this call invokes this get_queryset method with an
            # unsaved self.instance, which would trigger this query using the
            # default taggit logic:
            #
            #   TaggedPlace.objects.filter(content_object=Place())
            #
            # This works on Django < 5.0, returning an empty list as expected.
            # But as of Django 5.0, passing unsaved model instances to related
            # filters is no longer allowed, see
            # https://code.djangoproject.com/ticket/31486.
            #
            # To handle this case we return an empty tag list since there won't
            # be any existing tags in the database for an unsaved instance.
            elif self.instance.pk is None:
                return FakeQuerySet(self.through.tag_model(), [])

        # If we've reached this point then either this manager isn't associated
        # with a specific model, which probably means it's being invoked within
        # a prefetch_related operation:
        #
        #  Place.objects.prefetch_related("tags")
        #
        # or we're fetching tags for a model instance that doesn't have any
        # uncommitted tag changes in memory:
        #
        #   place = Place.objects.first()
        #   place.tags.all()
        #
        # In these cases we can fallback to the default taggit manager behavior
        # which will fetch the tags from the database.
        return super().get_queryset(extra_filters)

    @require_instance_manager
    def add(self, *tags):
        if TAGGIT_VERSION >= (3, 1, 0):
            self._remove_prefetched_objects()

        if TAGGIT_VERSION >= (1, 3, 0):
            tag_objs = self._to_tag_model_instances(tags, {})
        else:
            tag_objs = self._to_tag_model_instances(tags)

        # Now write these to the relation
        tagged_item_manager = self.get_tagged_item_manager()
        for tag in tag_objs:
            if not tagged_item_manager.filter(tag=tag):
                # make an instance of the self.through model and add it to the relation
                tagged_item = self.through(tag=tag)
                tagged_item_manager.add(tagged_item)

    @require_instance_manager
    def remove(self, *tags):
        if TAGGIT_VERSION >= (3, 1, 0):
            self._remove_prefetched_objects()

        tagged_item_manager = self.get_tagged_item_manager()
        tagged_items = [
            tagged_item for tagged_item in tagged_item_manager.all()
            if tagged_item.tag.name in tags
        ]
        tagged_item_manager.remove(*tagged_items)

    @require_instance_manager
    def set(self, *args, **kwargs):
        # Ignore the 'clear' kwarg (which defaults to False) and override it to be always true;
        # this means that set is implemented as a clear then an add, which was the standard behaviour
        # prior to django-taggit 0.19 (https://github.com/alex/django-taggit/commit/6542a702b590a5cfb91ea0de218b7f71ffd07c33).
        #
        # In this way, we avoid a live database lookup that occurs in the clear=False branch.
        #
        # The clear=True behaviour is fine for our purposes; the distinction only exists in django-taggit
        # to ensure that the correct set of m2m_changed signals is fired, and our reimplementation here
        # doesn't fire them at all (which makes logical sense, because the whole point of this module is
        # that the add/remove/set/clear operations don't write to the database).
        #
        # super().set() already calls self._remove_prefetched_objects() so we don't need to do so here.
        return super().set(*args, clear=True)

    @require_instance_manager
    def clear(self):
        if TAGGIT_VERSION >= (3, 1, 0):
            self._remove_prefetched_objects()
        self.get_tagged_item_manager().clear()


class ClusterTaggableManager(TaggableManager):
    _need_commit_after_assignment = True

    def __get__(self, instance, model):
        # override TaggableManager's requirement for instance to have a primary key
        # before we can access its tags
        manager = _ClusterTaggableManager(
            through=self.through, model=model, instance=instance, prefetch_cache_name=self.name
        )

        return manager

    def value_from_object(self, instance):
        # retrieve the queryset via the related manager on the content object,
        # to accommodate the possibility of this having uncommitted changes relative to
        # the live database
        rel_name = self.through._meta.get_field('content_object').remote_field.get_accessor_name()
        ret = getattr(instance, rel_name).all()
        if TAGGIT_VERSION >= (1, ):  # expects a Tag list instead of TaggedItem List
            ret = [tagged_item.tag for tagged_item in ret]
        return ret
