"""
Wagtail's hand-offs to its task framework, held to due-work-harness contracts.

Wagtail hands background work to Django's task framework: removing a deleted
image's or document's file from storage, and purging a published page's URLs
from the frontend cache (a CDN). These contracts run Wagtail's own test
project (``wagtail.test``) from this checkout with django-tasks-db's database
backend, and recovery is what production runs: ``manage.py db_worker``.
See README.md in this directory for how to run them.

Three contracts, each a declaration and one decorated class:

* ``WAGTAIL_MEDIA`` — deleting an image or a document through Wagtail's admin.
  The obligation: the file leaves storage.
* ``WAGTAIL_PUBLISHING`` — publishing a page. The obligation: the CDN stops
  serving the old page.
* ``DJANGO_TASKS_DB`` — django-tasks-db's worker running one of those tasks.
  The obligation: a task that ran is recorded as it ended, and a task that did
  not run is run.

What the harness finds is declared as legacy gaps, each a strict xfail
(https://github.com/wagtail/wagtail/issues/14652), and
``test_what_each_failure_costs`` pins every history, so a change in Wagtail
or in the harness shows exactly what moved. Beyond deaths after each commit,
the host fails each receiver of django.tasks' ``task_started`` and
``task_finished`` and of Wagtail's ``page_published``, as a receiver with a
bug or an unreachable backend would.
"""

from pathlib import Path
from typing import Any

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from due_work_harness import (
    Adoption,
    CallableDelivery,
    Decline,
    DueWorkContract,
    DueWorkSource,
    HandoffHistory,
    KnownGap,
    NotApplicable,
    Profile,
    SafetyContract,
    SafetyProfile,
    assert_pinned_outcomes,
    due_work_contract_suite,
    due_work_database,
)
from due_work_harness.crash_histories import ExternalCall
from due_work_harness.integrations.django_tasks import (
    RUNS_ONCE,
    TaskOutcome,
    db_worker_once,
    worker_contract,
)
from pydantic import BaseModel, ConfigDict

from wagtail.contrib.frontend_cache.tasks import purge_urls_from_cache_task
from wagtail.contrib.frontend_cache.utils import purge_urls_from_cache
from wagtail.documents import get_document_model
from wagtail.documents import signal_handlers as document_signal_handlers
from wagtail.images import get_image_model
from wagtail.images import signal_handlers as image_signal_handlers
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page, Site
from wagtail.test.customuser.models import CustomUser
from wagtail.test.testapp.models import SimplePage

from . import cdn

# The workers production runs, in batch mode: every ready task, then stop.
WORKER = CallableDelivery(name="wagtail on django-tasks-db", recover=db_worker_once())


def _editor() -> CustomUser:
    # ARRANGE: a superuser of Wagtail's test project (its AUTH_USER_MODEL) for the admin.
    return CustomUser.objects.filter(
        username="editor"
    ).first() or CustomUser.objects.create_superuser(
        username="editor", email="editor@example.com", password="password"
    )


class Media(BaseModel):
    """What a deleted image or document leaves behind."""

    model_config = ConfigDict(frozen=True)

    row: bool
    file_in_storage: bool


def an_image() -> tuple[int, str, Any]:
    # ARRANGE: an image with its file in storage.
    image = get_image_model().objects.create(
        title="a photo", file=get_test_image_file()
    )
    return image.pk, image.file.path, _editor()


def a_document() -> tuple[int, str, Any]:
    # ARRANGE: a document with its file in storage.
    document = get_document_model().objects.create(
        title="a contract", file=ContentFile(b"%PDF-1.4 signed", name="contract.pdf")
    )
    return document.pk, document.file.path, _editor()


def delete_the_image(handle: tuple[int, str, Any]) -> None:
    """Wagtail's own image delete view, through Django's full request stack."""
    client = Client()
    client.force_login(handle[2])
    response = client.post(f"/admin/images/{handle[0]}/delete/")
    assert response.status_code == 302, response.status_code


def delete_the_document(handle: tuple[int, str, Any]) -> None:
    """Wagtail's own document delete view, through Django's full request stack."""
    client = Client()
    client.force_login(handle[2])
    response = client.post(f"/admin/documents/delete/{handle[0]}/")
    assert response.status_code == 302, response.status_code


def image_left(handle: tuple[int, str, Any]) -> Media:
    # OBSERVE: whether the image row and its file still exist.
    return Media(
        row=get_image_model().objects.filter(pk=handle[0]).exists(),
        file_in_storage=Path(handle[1]).exists(),
    )


def document_left(handle: tuple[int, str, Any]) -> Media:
    # OBSERVE: whether the document row and its file still exist.
    return Media(
        row=get_document_model().objects.filter(pk=handle[0]).exists(),
        file_in_storage=Path(handle[1]).exists(),
    )


DELETE_IMAGE = HandoffHistory(
    name="delete image",
    arrange=an_image,
    transition=delete_the_image,
    observe=image_left,
)
DELETE_DOCUMENT = HandoffHistory(
    name="delete document",
    arrange=a_document,
    transition=delete_the_document,
    observe=document_left,
)

WHY_NO_SWEEP = (
    "nothing Wagtail runs looks for a file whose image or document row is gone: a file whose deletion task was "
    "never enqueued, or failed, stays in storage forever "
    "(https://github.com/wagtail/wagtail/issues/14652)"
)
WHY_NO_RETRY = f"{RUNS_ONCE}, so a storage error fails the deletion for good"

WAGTAIL_MEDIA = DueWorkContract(
    name="wagtail: deleting an image or a document",
    adoption=Adoption.LEGACY,
    transactional=True,
    profiles={
        Profile.A: KnownGap(WHY_NO_SWEEP),
        Profile.B: Decline(
            "the task is claimed by django-tasks-db's worker, whose contract is DJANGO_TASKS_DB"
        ),
        Profile.C: NotApplicable(
            "deleting a file is idempotent: a repeat deletes nothing"
        ),
        Profile.D: NotApplicable(
            "the obligation holds no rows of its own; the task's row is django-tasks-db's"
        ),
        Profile.E: NotApplicable(
            "each deletion removes one file; no two results race to write it"
        ),
        Profile.F: KnownGap(
            "no product state records that a file is still to be deleted once its row is gone, so no recovery "
            "can derive the obligation"
        ),
    },
    safety=SafetyContract(
        name="wagtail: deleting an image or a document",
        adoption=Adoption.LEGACY,
        profiles={
            SafetyProfile.REPLAY_SAFE_EXECUTION: NotApplicable(
                "a repeated deletion deletes nothing"
            ),
            SafetyProfile.BOUNDED_RETRY: NotApplicable(WHY_NO_RETRY),
        },
    ),
    handoffs=(DELETE_IMAGE, DELETE_DOCUMENT),
    handoff_delivery=WORKER,
    handoff_gaps=dict.fromkeys(
        ("delete image", "delete document"),
        "the delete view commits the row, then enqueues delete_file_from_storage_task from "
        "transaction.on_commit, in its own autocommit write. A death between the two, or a "
        "failing enqueue, leaves the file in storage with nothing to delete it; served "
        "straight from storage, a deleted original stays reachable at its URL "
        "(https://github.com/wagtail/wagtail/issues/14652). test_what_each_failure_costs "
        "pins each history",
    ),
)


@due_work_contract_suite(
    WAGTAIL_MEDIA,
    covers=(
        DueWorkSource(image_signal_handlers.post_delete_file_cleanup, sites=2),
        DueWorkSource(document_signal_handlers.post_delete_file_cleanup, sites=2),
    ),
)
class TestWagtailMedia:
    pass


class Published(BaseModel):
    """What a visitor gets: the page's live content, and whether the CDN was told to drop the old copy."""

    model_config = ConfigDict(frozen=True)

    live_content: str
    purges: int


def a_live_page() -> tuple[int, str, Any]:
    # ARRANGE: a live page, served through the CDN, with no purge owed.
    root = Site.objects.get(is_default_site=True).root_page
    page = root.add_child(
        instance=SimplePage(
            title="Opening hours",
            slug=f"hours-{Page.objects.count()}",
            content="9 to 5",
        )
    )
    page.save_revision().publish()
    db_worker_once()()
    cdn.PURGED.clear()
    return page.pk, page.get_full_url(), _editor()


def publish_new_hours(handle: tuple[int, str, Any]) -> None:
    """Wagtail's publish, as its page editor calls it: a new revision, published by the editor."""
    page = Page.objects.get(pk=handle[0]).specific
    page.content = "10 to 6"
    page.save_revision(user=handle[2]).publish(user=handle[2])


def what_visitors_get(handle: tuple[int, str, Any]) -> Published:
    # OBSERVE: the live page's content, and how many times the CDN was asked to purge its URL.
    return Published(
        live_content=Page.objects.get(pk=handle[0]).specific.content,
        purges=cdn.PURGED[handle[1]],
    )


PUBLISH_PAGE = HandoffHistory(
    name="publish page",
    arrange=a_live_page,
    transition=publish_new_hours,
    observe=what_visitors_get,
)

WAGTAIL_PUBLISHING = DueWorkContract(
    name="wagtail: publishing a page behind a CDN",
    adoption=Adoption.LEGACY,
    transactional=True,
    profiles={
        Profile.A: KnownGap(
            "nothing Wagtail runs looks for a page published since its last purge: a purge that was never "
            "enqueued, or failed, leaves the CDN serving the old page until its cache expires "
            "(https://github.com/wagtail/wagtail/issues/14652)"
        ),
        Profile.B: Decline(
            "the task is claimed by django-tasks-db's worker, whose contract is DJANGO_TASKS_DB"
        ),
        Profile.C: NotApplicable(
            "purging a URL is idempotent: a repeat purges nothing new"
        ),
        Profile.D: NotApplicable(
            "the obligation holds no rows of its own; the task's row is django-tasks-db's"
        ),
        Profile.E: NotApplicable(
            "each purge invalidates a URL; no two results race to write it"
        ),
        Profile.F: KnownGap(
            "no product state records that a published page is still to be purged, so no recovery can derive "
            "the obligation"
        ),
    },
    safety=SafetyContract(
        name="wagtail: publishing a page behind a CDN",
        adoption=Adoption.LEGACY,
        profiles={
            SafetyProfile.REPLAY_SAFE_EXECUTION: NotApplicable(
                "a repeated purge purges nothing new"
            ),
            SafetyProfile.BOUNDED_RETRY: NotApplicable(
                f"{RUNS_ONCE}, so a CDN error fails the purge"
            ),
        },
    ),
    handoffs=(PUBLISH_PAGE,),
    handoff_delivery=WORKER,
    handoff_gaps={
        "publish page": (
            "publishing commits the page in several autocommit writes and enqueues the purge in a later one, "
            "from the page_published signal: a death between the page going live and the enqueue, or a "
            "page_published receiver failing ahead of the frontend cache's, leaves the new content live and "
            "the old one cached (https://github.com/wagtail/wagtail/issues/14652). "
            "test_what_each_failure_costs pins each history"
        )
    },
)


@due_work_contract_suite(
    WAGTAIL_PUBLISHING, covers=(DueWorkSource(purge_urls_from_cache),)
)
class TestWagtailPublishing:
    pass


URL = "http://localhost/opening-hours/"


def a_purge_owed() -> str:
    # ARRANGE: a frontend cache purge enqueued by Wagtail's own task, ready for a worker.
    cdn.PURGED.clear()
    return str(purge_urls_from_cache_task.enqueue([URL]).id)


def purges(_task_id: str) -> int:
    # OBSERVE: how many times the CDN purged the task's URL.
    return cdn.PURGED[URL]


# django-tasks-db's own contract with its worker, bound to Wagtail's purge task: the framework's
# dispositions, retention and gap probes come from the integration.
DJANGO_TASKS_DB = worker_contract(
    name="django-tasks-db: the worker running Wagtail's tasks",
    enqueue=a_purge_owed,
    effect=purges,
    # EXTERNAL SEAM: the CDN's purge API.
    external_calls=(ExternalCall(owner=cdn.RecordingCDN, attribute="purge"),),
    delivery=WORKER,
)
WORKER_RUNS_A_PURGE = DJANGO_TASKS_DB.handoffs[0]


@due_work_contract_suite(DJANGO_TASKS_DB)
class TestDjangoTasksDb:
    pass


# What each history leaves after the worker runs again, pinned: every entry but the
# benign ones is a loss the site's visitors, its editors or its storage bill see.
KEPT = Media(row=True, file_in_storage=True)
DELETED = Media(row=False, file_in_storage=False)
ORPHANED = Media(row=False, file_in_storage=True)
OLD_CONTENT = Published(live_content="9 to 5", purges=0)
PURGED = Published(live_content="10 to 6", purges=1)
STALE = Published(live_content="10 to 6", purges=0)

MEDIA_FINDINGS = {
    # Benign: the request died before the row was deleted; the editor sees an error and can try again.
    **{f"worker died after commit {k}": KEPT for k in range(1, 7)},
    # FINDING: the row is deleted and the file stays in storage, with nothing left to delete it.
    "worker died after commit 7": ORPHANED,
    "worker died after commit 8": DELETED,
    "after-commit callback 1 failed": ORPHANED,
}

PUBLISH_FINDINGS = {
    # Benign: the new revision never went live.
    "worker died after commit 1": OLD_CONTENT,
    "worker died after commit 2": OLD_CONTENT,
    # FINDING: the new content is live and the CDN keeps serving the old page.
    "worker died after commit 3": STALE,
    "worker died after commit 4": PURGED,
    "worker died after commit 5": PURGED,
    # FINDING: no death at all. The frontend cache's page_published receiver raises (its CDN API
    # unreachable, or a bug), and the publish has already committed.
    "signal receiver 1 failed": STALE,
}


def _task(status: str, purges: int) -> TaskOutcome:
    return TaskOutcome(status=status, effect=purges)


WORKER_FINDINGS = {
    # FINDING (known upstream): the claim committed, the worker died, and the task stays RUNNING forever.
    "worker died after commit 1": _task("RUNNING", 0),
    "worker died after commit 2": _task("SUCCESSFUL", 1),
    "worker died after commit 3": _task("SUCCESSFUL", 1),
    # FINDING: the purge happened and the task stays RUNNING forever.
    "worker died after external call 1": _task("RUNNING", 1),
    # FINDING: task_started's receiver raised, so the task is FAILED without running, and nothing retries it.
    "signal receiver 1 failed": _task("FAILED", 0),
    # FINDING: task_finished's receiver raised after the task ran, and its SUCCESSFUL record was rewritten as FAILED.
    "signal receiver 2 failed": _task("FAILED", 1),
}


@due_work_database()
@pytest.mark.parametrize(
    ("history", "delivered", "findings"),
    [
        pytest.param(DELETE_IMAGE, DELETED, MEDIA_FINDINGS, id="delete image"),
        pytest.param(DELETE_DOCUMENT, DELETED, MEDIA_FINDINGS, id="delete document"),
        pytest.param(PUBLISH_PAGE, PURGED, PUBLISH_FINDINGS, id="publish page"),
        pytest.param(
            WORKER_RUNS_A_PURGE, _task("SUCCESSFUL", 1), WORKER_FINDINGS, id="worker"
        ),
    ],
)
def test_what_each_failure_costs(
    history: HandoffHistory, delivered: Any, findings: dict[str, Any]
) -> None:
    assert_pinned_outcomes(WORKER, history, delivered=delivered, outcomes=findings)
