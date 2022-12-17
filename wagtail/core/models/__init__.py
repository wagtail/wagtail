from warnings import warn

from wagtail.models import (  # noqa
    COMMENTS_RELATION_NAME,
    PAGE_MODEL_CLASSES,
    PAGE_PERMISSION_TYPE_CHOICES,
    PAGE_PERMISSION_TYPES,
    PAGE_TEMPLATE_VAR,
    AbstractPage,
    BasePageManager,
    Comment,
    CommentReply,
    GroupApprovalTask,
    GroupPagePermission,
    Orderable,
    Page,
    PageBase,
    PageLogEntry,
    PageLogEntryManager,
    PageLogEntryQuerySet,
    PageManager,
    PagePermissionTester,
    PageSubscription,
    PageViewRestriction,
    Revision,
    SubmittedRevisionsManager,
    Task,
    TaskManager,
    TaskState,
    TaskStateManager,
    UserPagePermissionsProxy,
    Workflow,
    WorkflowManager,
    WorkflowPage,
    WorkflowState,
    WorkflowStateManager,
    WorkflowTask,
    get_default_page_content_type,
    get_page_models,
    get_streamfield_names,
    logger,
    reassign_root_page_locale_on_delete,
)
from wagtail.utils.deprecation import RemovedInWagtail50Warning

from .audit_log import (  # noqa
    BaseLogEntry,
    BaseLogEntryManager,
    LogEntryQuerySet,
    ModelLogEntry,
)
from .collections import (  # noqa
    BaseCollectionManager,
    Collection,
    CollectionManager,
    CollectionMember,
    CollectionViewRestriction,
    GroupCollectionPermission,
    GroupCollectionPermissionManager,
    get_root_collection_id,
)
from .copying import _copy, _copy_m2m_relations, _extract_field_data  # noqa
from .i18n import (  # noqa
    BootstrapTranslatableMixin,
    BootstrapTranslatableModel,
    Locale,
    LocaleManager,
    TranslatableMixin,
    bootstrap_translatable_model,
    get_translatable_models,
)
from .sites import Site, SiteManager, SiteRootPath  # noqa

warn(
    "Importing from wagtail.core.models is deprecated. "
    "Use wagtail.models instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
