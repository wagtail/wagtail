from ninja import Router

from wagtail.api.v3.routers.pages import list_pages

from .schemas import AdminPageSchema

router = Router(tags=["pages"])

router.get(
    "/",
    response=list[AdminPageSchema],
    url_name="list_pages",
    summary="List pages",
    operation_id="pages_list",
)(list_pages)
