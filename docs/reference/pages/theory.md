(pages_theory)=

# Theory

## Introduction to trees

If you're unfamiliar with trees as an abstract data type, you might want to [review the concepts involved](<https://en.wikipedia.org/wiki/Tree_(data_structure)>).

As a web developer, though, you probably already have a good understanding of trees as filesystem directories or paths. Wagtail pages can create the same structure, as each page in the tree has its own URL path, like so:

```
/
    people/
        nien-nunb/
        laura-roslin/
    events/
        captain-picard-day/
        winter-wrap-up/
```

The Wagtail admin interface uses the tree to organize content for editing, letting you navigate up and down levels in the tree through its Explorer menu. This method of organization is a good place to start in thinking about your own Wagtail models.

### Nodes and leaves

It might be handy to think of the `Page`-derived models you want to create as being one of two node types: parents and leaves. Wagtail isn't prescriptive in this approach, but it's a good place to start if you're not experienced in structuring your own content types.

#### Nodes

Parent nodes on the Wagtail tree probably want to organize and display a browseable index of their descendants. A blog, for instance, needs a way to show a list of individual posts.

A Parent node could provide its own function returning its descendant objects.

```python
class EventPageIndex(Page):
    # ...
    def events(self):
        # Get the list of live event pages that are descendants of this page
        events = EventPage.objects.live().descendant_of(self)

        # Filter events list to get ones that are either
        # running now or start in the future
        events = events.filter(date_from__gte=date.today())

        # Order by date
        events = events.order_by('date_from')

        return events
```

This example makes sure to limit the returned objects to pieces of content that make sense, specifically ones that have been published through Wagtail's admin interface (`live()`) and are children of this node (`descendant_of(self)`). By setting a `subpage_types` class property in your model, you can specify which models are allowed to be set as children, and by setting a `parent_page_types` class property, you can specify which models are allowed to be parents of this page model. Wagtail will allow any `Page`-derived model by default. Regardless, it's smart for a parent model to provide an index filtered to make sense.

#### Leaves

Leaves are the pieces of content itself, a consumable page, and might just consist of a bunch of properties. A blog page leaf might have some body text and an image. A person's page leaf might have a photo, a name, and an address.

It might be helpful for a leaf to provide a way to back up along the tree to a parent, such as in the case of breadcrumbs navigation. The tree might also be deep enough that a leaf's parent won't be included in general site navigation.

The model for the leaf could provide a function that traverses the tree in the opposite direction and returns an appropriate ancestor:

```python
class EventPage(Page):
    # ...
    def event_index(self):
        # Find the closest ancestor which is an event index
        return self.get_ancestors().type(EventIndexPage).last()
```

If defined, `subpage_types` and `parent_page_types` will also limit the parent models allowed to contain a leaf. If not, Wagtail will allow any combination of parents and leafs to be associated in the Wagtail tree. Like with index pages, it's a good idea to make sure that the index is actually of the expected model to contain the leaf.

#### Other relationships

Your `Page`-derived models might have other interrelationships that extend the basic Wagtail tree or depart from it entirely. You could provide functions to navigate between siblings, such as a "Next Post" link on a blog page (`post->post->post`). It might make sense for subtrees to interrelate, such as in a discussion forum (`forum->post->replies`) Skipping across the hierarchy might make sense, too, as all objects of a certain model class might interrelate regardless of their ancestors (`events = EventPage.objects.all`). It's largely up to the models to define their interrelations, the possibilities are endless.

(anatomy_of_a_wagtail_request)=

## Anatomy of a Wagtail request

For going beyond the basics of model definition and interrelation, it might help to know how Wagtail handles requests and constructs responses. In short, it goes something like:

1.  Django gets a request and routes through Wagtail's URL dispatcher definitions
2.  Wagtail checks the hostname of the request to determine which `Site` record will handle this request.
3.  Starting from the root page of that site, Wagtail traverses the page tree, calling the `route()` method and letting each page model decide whether it will handle the request itself or pass it on to a child page.
4.  The page responsible for handling the request returns a `RouteResult` object from `route()`, which identifies the page along with any additional `args`/`kwargs` to be passed to `serve()`.
5.  Wagtail calls `serve()`, which constructs a context using `get_context()`
6.  `serve()` finds a template to pass it to using `get_template()`
7.  A response object is returned by `serve()` and Django responds to the requester.

You can apply custom behavior to this process by overriding `Page` class methods such as `route()` and `serve()` in your own models. For examples, see [Recipes](page_model_recipes).

(scheduled_publishing)=

## Scheduled publishing

Page publishing can be scheduled through the _Set schedule_ feature in the _Status_ side panel of the _Edit_ page. This allows you to set up initial page publishing or a page update in advance.
For pages to go live at the scheduled time, you should set up the [publish_scheduled](publish_scheduled) management command.

### Basic workflow for scheduled publishing

-   Scheduling is done by setting the _go-live at_ field of the page and clicking _Publish_.
-   Scheduling a revision for a page that is not currently live means that page will go live when the scheduled time comes.
-   Scheduling a revision for a page that is already live means that the revision will be published when the time comes.
-   If the page has a scheduled revision and you set another revision to publish immediately (i.e. clicking _Publish_ with the _go-live at_ field unset), the scheduled revision will be unscheduled.
-   If the page has a scheduled revision and you schedule another revision to publish (i.e. clicking _Publish_ with the _go-live at_ field set), the existing scheduled revision will be unscheduled and the new revision will be scheduled instead.

```{note}
You must click _Publish_ after setting the _go-live at_ field for the revision to be scheduled. Saving a draft revision with the _go-live at_ field without clicking _Publish_ will not schedule it to be published.
```

### Viewing and managing scheduled revisions

The _History_ view for a given page will show which revision is scheduled and when it is scheduled. A scheduled revision in the list will also provide an _Unschedule_ button to cancel it.

## Scheduled unpublishing

In addition to scheduling a page to be published, it is also possible to schedule a page to be unpublished by setting the _expire at_ field. However, unlike with publishing, the unpublishing schedule is applied to the live page instance rather than a specific revision. This means that any change to the _expire at_ field will only be effective once the associated revision is published (i.e. when the changes are applied to the live instance). To illustrate:

### Basic workflow for scheduled unpublishing

-   Scheduling is done by setting the _expire at_ field of the page and clicking _Publish_. If the _go-live at_ field is also set, then the unpublishing schedule will only be applied after the revision goes live.
-   Consider a live page that is scheduled to be unpublished on e.g. 14 June. Then sometime before the schedule, consider that a new revision is scheduled to be published on a date that's **earlier** than the unpublishing schedule, e.g. 9 June. When the new revision goes live on 9 June, the _expire at_ field contained in the new revision will replace the existing unpublishing schedule. This means:
    -   If the new revision contains a different _expire at_ field (e.g. 17 June), the new revision will go live on 9 June and the page will not be unpublished on 14 June but will be unpublished on 17 June.
    -   If the new revision has the _expire at_ field unset, the new revision will go live on 9 June and the unpublishing schedule will be unset, thus the page will not be unpublished.
-   Consider another live page that is scheduled to be unpublished on e.g. 14 June. Then sometime before the schedule, consider that a new revision is scheduled to be published on a date that's **later** than the unpublishing schedule, e.g. 21 June. The new revision will not take effect until it goes live on 21 June, so the page will still be unpublished on 14 June. This means:
    -   If the new revision contains a different _expire at_ field (e.g. 25 June), the page will be unpublished on 14 June, the new revision will go live on 21 June and the page will be unpublished again on 25 June.
    -   If the new revision has the _expire at_ field unset, the page will be unpublished on 14 June and the new revision will go live on 21 June.

```{note}
The same scheduling mechanism also applies to snippets with {class}`~wagtail.models.DraftStateMixin` applied. For more details, see [](wagtailsnippets_saving_draft_changes_of_snippets).
```
