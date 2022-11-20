(management_commands)=

# Management commands

(publish_scheduled)=

## publish_scheduled

```{versionchanged} 4.1
This command has been renamed from `publish_scheduled_pages` to `publish_scheduled` and it now also handles non-page objects.
The `publish_scheduled_pages` command is still available as an alias, but it is recommended to update your configuration to run the `publish_scheduled` command instead.
```

```sh
./manage.py publish_scheduled
```

This command publishes, updates or unpublishes objects that have had these actions scheduled by an editor. We recommend running this command once an hour.

(fixtree)=

## fixtree

```sh
./manage.py fixtree
```

This command scans for errors in your database and attempts to fix any issues it finds.

(move_pages)=

## move_pages

```sh
manage.py move_pages from to
```

This command moves a selection of pages from one section of the tree to another.

Options:

-   **from**
    This is the **id** of the page to move pages from. All descendants of this page will be moved to the destination. After the operation is complete, this page will have no children.

-   **to**
    This is the **id** of the page to move pages to.

(purge_revisions)=

## purge_revisions

```sh
manage.py purge_revisions [--days=<number of days>]
```

This command deletes old page revisions which are not in moderation, live, approved to go live, or the latest
revision for a page. If the `days` argument is supplied, only revisions older than the specified number of
days will be deleted.

(purge_embeds)=

## purge_embeds

```sh
manage.py purge_embeds
```

This command deletes all the cached embed objects from the database. It is recommended to run this command after changes are made to any embed settings so that subsequent embed usage does not from the database cache.

(update_index)=

## update_index

```sh
./manage.py update_index [--backend <backend name>]
```

This command rebuilds the search index from scratch.

It is recommended to run this command once a week and at the following times:

-   whenever any pages have been created through a script (after an import, for example)
-   whenever any changes have been made to models or search configuration

The search may not return any results while this command is running, so avoid running it at peak times.

### Specifying which backend to update

By default, `update_index` will rebuild all the search indexes listed in `WAGTAILSEARCH_BACKENDS`.

If you have multiple backends and would only like to update one of them, you can use the `--backend` option.

For example, to update just the default backend:

```sh
python manage.py update_index --backend default
```

The `--chunk_size` option can be used to set the size of chunks that are indexed at a time. This defaults to
1000 but may need to be reduced for larger document sizes.

### Indexing the schema only

You can prevent the `update_index` command from indexing any data by using the `--schema-only` option:

```sh
python manage.py update_index --schema-only
```

### Silencing the command

You can prevent logs to the console by providing `--verbosity 0` as an argument:

```sh
python manage.py update_index --verbosity 0
```

If this is omitted or provided with any number above 0 it will produce the same logs.

(wagtail_update_index)=

## wagtail_update_index

An alias for the `update_index` command that can be used when another installed package (such as [Haystack](https://haystacksearch.org/)) provides a command named `update_index`. In this case, the other package's entry in `INSTALLED_APPS` should appear above `wagtail.search` so that its `update_index` command takes precedence over Wagtail's.

(search_garbage_collect)=

## rebuild_references_index

```sh
./manage.py rebuild_references_index
```

This command populates the table that tracks cross-references between objects, used for the usage reports on images, documents and snippets. This table is updated automatically saving objects, but it is recommended to run this command periodically to ensure that the data remains consistent.

### Silencing the command

You can prevent logs to the console by providing `--verbosity 0` as an argument:

```sh
python manage.py rebuild_references_index --verbosity 0
```

## search_garbage_collect

```sh
./manage.py search_garbage_collect
```

Wagtail keeps a log of search queries that are popular on your website. On high traffic websites, this log may get big and you may want to clean out old search queries. This command cleans out all search query logs that are more than one week old (or a number of days configurable through the [`WAGTAILSEARCH_HITS_MAX_AGE`](wagtailsearch_hits_max_age) setting).

(wagtail_update_image_renditions)=

## wagtail_update_image_renditions

```sh
./manage.py wagtail_update_image_renditions
```

This command provides the ability to regenerate image renditions.
This is useful if you have deployed to a server where the image renditions have not yet been generated or you have changed the underlying image rendition behaviour and need to ensure all renditions are created again.

This does not remove rendition images that are unused, this can be done by clearing the folder using `rm -rf` or similar, once this is done you can then use the management command to generate the renditions.

Options:

-   **--purge-only** :
    This argument will purge all image renditions without regenerating them. They will be regenerated when next requested.
