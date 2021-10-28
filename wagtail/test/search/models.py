from django.db import models
from taggit.managers import TaggableManager

from wagtail.search import index


class Author(index.Indexed, models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True)

    search_fields = [
        index.SearchField('name'),
        index.AutocompleteField('name'),
        index.FilterField('date_of_birth'),
    ]

    def __str__(self):
        return self.name


class Book(index.Indexed, models.Model):
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author, related_name='books')
    publication_date = models.DateField()
    number_of_pages = models.IntegerField()
    tags = TaggableManager()

    search_fields = [
        index.SearchField('title', partial_match=True, boost=2.0),
        index.AutocompleteField('title'),
        index.FilterField('title'),
        index.FilterField('authors'),
        index.RelatedFields('authors', Author.search_fields),
        index.FilterField('publication_date'),
        index.FilterField('number_of_pages'),
        index.RelatedFields('tags', [
            index.SearchField('name'),
            index.FilterField('slug'),
        ]),
        index.FilterField('tags'),
    ]

    @classmethod
    def get_indexed_objects(cls):
        indexed_objects = super(Book, cls).get_indexed_objects()

        # Don't index books using Book class that they have a more specific type
        if cls is Book:
            indexed_objects = indexed_objects.exclude(
                id__in=Novel.objects.values_list('book_ptr_id', flat=True)
            )

            indexed_objects = indexed_objects.exclude(
                id__in=ProgrammingGuide.objects.values_list('book_ptr_id', flat=True)
            )

        # Exclude Books that have the title "Don't index me!"
        indexed_objects = indexed_objects.exclude(title="Don't index me!")

        return indexed_objects

    def get_indexed_instance(self):
        # Check if this object is a Novel or ProgrammingGuide and return the specific object
        novel = Novel.objects.filter(book_ptr_id=self.id).first()
        programming_guide = ProgrammingGuide.objects.filter(book_ptr_id=self.id).first()

        # Return the novel/programming guide object if there is one, otherwise return self
        return novel or programming_guide or self

    def __str__(self):
        return self.title


class Character(models.Model):
    name = models.CharField(max_length=255)
    novel = models.ForeignKey('Novel', related_name='characters', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Novel(Book):
    setting = models.CharField(max_length=255)
    protagonist = models.OneToOneField(Character, related_name='+', null=True, on_delete=models.SET_NULL)

    search_fields = Book.search_fields + [
        index.SearchField('setting', partial_match=True),
        index.RelatedFields('characters', [
            index.SearchField('name', boost=0.25),
        ]),
        index.RelatedFields('protagonist', [
            index.SearchField('name', boost=0.5),
            index.FilterField('novel'),
        ]),
        index.FilterField('protagonist'),
    ]


class ProgrammingGuide(Book):
    programming_language = models.CharField(max_length=255, choices=[
        ('py', "Python"),
        ('js', "JavaScript"),
        ('rs', "Rust"),
    ])

    search_fields = Book.search_fields + [
        index.SearchField('get_programming_language_display'),
        index.FilterField('programming_language'),
    ]
