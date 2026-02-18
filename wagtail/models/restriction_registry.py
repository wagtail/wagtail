from django.utils.translation import gettext_lazy as _

class RestrictionRegistry:
    """
    A central registry for pluggable view restriction types and their 
    associated permission-checking logic.
    """

    def __init__(self):
        self._registry = {
            'none': {'label': 'Public', 'check': None},
            'password': {'label': 'shared password', 'check': None},
            'login': {'label': 'private, accessible to any logged-in users', 'check': None},
            'groups': {'label': 'private, accessible to users in specific groups', 'check': None},
        }

    def register(self, key, label, check_func):
        self._registry[key] = {'label': label, 'check': check_func}

    def get_choices(self):
        return [(k, v['label']) for k, v in self._registry.items()]

    def get_check(self, key):
        return self._registry.get(key, {}).get('check')

# --- 1. CREATE THE OBJECT FIRST ---
restriction_registry = RestrictionRegistry()

# --- 2. NOW YOU CAN REGISTER (If you want to do it here) ---
# (Usually, it's better to keep this file clean and register in test_plugin.py)