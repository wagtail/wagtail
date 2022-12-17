from warnings import warn

# Import block types defined in submodules into the wagtail.blocks namespace
from wagtail.blocks.base import *  # NOQA
from wagtail.blocks.field_block import *  # NOQA
from wagtail.blocks.list_block import *  # NOQA
from wagtail.blocks.static_block import *  # NOQA
from wagtail.blocks.stream_block import *  # NOQA
from wagtail.blocks.struct_block import *  # NOQA
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.blocks is deprecated. "
    "Use wagtail.blocks instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
