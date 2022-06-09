from pattern_library.monkey_utils import override_tag
from wagtail.admin.templatetags.wagtailadmin_tags import register


override_tag(register, name="avatar_url")
