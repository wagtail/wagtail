from django.conf import settings

from wagtail.admin.ui.components import Component


class EditingSessionsModule(Component):
    template_name = "wagtailadmin/shared/editing_sessions/module.html"

    def __init__(
        self,
        current_session,
        ping_url,
        release_url,
        other_sessions,
        revision_id=None,
    ):
        self.current_session = current_session
        self.ping_url = ping_url
        self.release_url = release_url
        self.sessions_list = EditingSessionsList(current_session, other_sessions)
        self.revision_id = revision_id

    def get_context_data(self, parent_context):
        ping_interval = getattr(
            settings,
            "WAGTAIL_EDITING_SESSION_PING_INTERVAL",
            10000,
        )
        return {
            "current_session": self.current_session,
            "ping_url": self.ping_url,
            "release_url": self.release_url,
            "ping_interval": ping_interval,
            "sessions_list": self.sessions_list,
            "revision_id": self.revision_id,
        }


class EditingSessionsList(Component):
    template_name = "wagtailadmin/shared/editing_sessions/list.html"

    def __init__(self, current_session, other_sessions):
        self.current_session = current_session
        self.sessions = other_sessions

    def get_context_data(self, parent_context):
        return {"current_session": self.current_session, "sessions": self.sessions}
