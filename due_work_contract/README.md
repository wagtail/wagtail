# Due-work contracts for Wagtail's task hand-offs

[due-work-harness](https://github.com/gigaverse-app/due-work-harness) contracts for the
background work Wagtail hands to Django's task framework, and what happens to it when a
process dies or a hand-off fails between commits
([#14652](https://github.com/wagtail/wagtail/issues/14652)):

- deleting an image or a document: the file must leave storage;
- publishing a page: the frontend cache must stop serving the old page;
- django-tasks-db's worker running one of those tasks.

They run Wagtail's own test project (`wagtail.test.settings`) on PostgreSQL with
django-tasks-db's database backend, recovering with `db_worker`, as a deployment would.
Each gap the harness finds is a strict xfail, and each history's `findings` pins what
every run leaves behind, in the same run.

This directory is separate from Wagtail's test suite: it is pytest-based, it is not
collected by `runtests.py` (its tests are in `*_test.py`, which pytest
collects and Django's `test*.py` discovery does not), it is not packaged, and its
dependencies are not part of Wagtail's `testing` extra.

## Running

It needs PostgreSQL (the `PG*` environment variables; the database is created by the
run) and, on top of Wagtail's testing dependencies:

```sh
pip install -e ".[testing]"
pip install "due-work-harness>=0.5.0" django-tasks-db "psycopg[binary]" pytest pytest-django
cd due_work_contract
PGHOST=localhost PGUSER=postgres PGPASSWORD=postgres pytest --create-db --due-work-verify
```

`due-work-harness check --root due_work_contract` checks that every hand-off in the
`wagtail` package is covered by a contract here or listed in the baseline in
`pyproject.toml`.
