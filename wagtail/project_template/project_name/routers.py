import sys
import threading
from django.conf import settings

_local = threading.local()


SHARED_APPS = []


def get_database_from_command_line():
    args = sys.argv
    for i, arg in enumerate(args):
        if arg == '--database':
            if i + 1 < len(args):
                return args[i + 1]
        elif arg.startswith('--database='):
            return arg.split('=', 1)[1]
    return "default"


def set_current_tenant(tenant_db):
    _local.tenant = tenant_db


def get_current_tenant():
    tenant = getattr(_local, 'tenant', None)
    if not tenant:
        tenant = get_database_from_command_line()
    return tenant


def clear_current_tenant():
    if hasattr(_local, 'tenant'):
        del _local.tenant


class TenantRouter:
    """
    A router to control all database operations on models for different tenants.
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label in SHARED_APPS:
            return 'default'
        if "instance" in hints and hints["instance"] is not None:
            return hints["instance"]._state.db
        if "using" in hints:
            return hints["using"]
        return get_current_tenant()

    def db_for_write(self, model, **hints):
        if model._meta.app_label in SHARED_APPS:
            return 'default'
        if "instance" in hints and hints["instance"] is not None:
            return hints["instance"]._state.db
        if "using" in hints:
            return hints["using"]
        return get_current_tenant()

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db in settings.DATABASES
