from wagtail.contrib.search_promotions.models import SearchPromotion
from wagtail.permissions import get_permission_policy, model_permission_policy_class


permission_policy = get_permission_policy("search_promotion", default=model_permission_policy_class)(SearchPromotion)