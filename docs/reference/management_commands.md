(management_commands)=

# Management commands

(wagtail_start)=

## start

By default, the `start` command creates a project template, which contains your `models.py`, templates, and settings files. For example, to create new Wagtail project named `mysite`, use the command like this:

```sh
wagtail start mysite
```

You can also use the `--template` option with the `start` command to generate a custom template. See [`The project template`](project_templates_reference) for more information on how the command works with default and custom templates.

(publish_scheduled)=

## publish_scheduled

```sh
./manage.py publish_scheduled
```

This command publishes, updates, or unpublishes objects that have had these actions scheduled by an editor. We recommend running this command once an hour.

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
manage.py purge_revisions [--days=<number of days>] [--pages] [--non-pages]
```

This command deletes old revisions which are not in moderation, live, approved to go live, or the latest
revision. If the `days` argument is supplied, only revisions older than the specified number of
days will be deleted.

To prevent deleting important revisions when they become stale, you can refer to such revisions in a model using a `ForeignKey` with {attr}`on_delete=models.PROTECT <django.db.models.PROTECT>`.

If the `pages` argument is supplied, only revisions of page models will be deleted. If the `non-pages` argument is supplied, only revisions of non-page models will be deleted. If both or neither arguments are supplied, revisions of all models will be deleted.
If deletion of a revision is not desirable, mark `Revision` with `on_delete=models.PROTECT`.

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

## rebuild_references_index

```sh
./manage.py rebuild_references_index
```

This command populates the table that tracks cross-references between objects, used for the usage reports on images, documents, and snippets. This table is updated automatically saving objects, but it is recommended to run this command periodically to ensure that the data remains consistent.

### Silencing the command

You can prevent logs to the console by providing `--verbosity 0` as an argument:

```sh
python manage.py rebuild_references_index --verbosity 0
```

## show_references_index

```sh
./manage.py show_references_index
```

Displays a summary of the contents of the references index. This shows the number of objects indexed against each model type and can be useful to identify which models are being indexed without rebuilding the index itself.

(wagtail_update_image_renditions)=

## wagtail_update_image_renditions

```sh
./manage.py wagtail_update_image_renditions
```

This command provides the ability to regenerate image renditions.
This is useful if you have deployed to a server where the image renditions have not yet been generated or you have changed the underlying image rendition behavior and need to ensure all renditions are created again.

This does not remove unused rendition images, this can be done by clearing the folder using `rm -rf` or similar, once this is done you can then use the management command to generate the renditions.

Options:

-   `--purge-only` :
    This argument will purge all image renditions without regenerating them. They will be regenerated when next requested.

(convert_mariadb_uuids)=

## convert_mariadb_uuids

```sh
./manage.py convert_mariadb_uuids
```

For sites using MariaDB, this command must be run once when upgrading to Django 5.0 and MariaDB 10.7 from any earlier version of Django or MariaDB. This is necessary because Django 5.0 introduces support for MariaDB's native UUID type, breaking backwards compatibility with `CHAR`-based UUIDs used in earlier versions of Django and MariaDB. New sites created under Django 5.0+ and MariaDB 10.7+ are unaffected.
