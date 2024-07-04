from wagtail.admin.ui.components import Component


class EditingSessionsModule(Component):
    template_name = "wagtailadmin/shared/editing_sessions/module.html"

    def __init__(self, ping_url, release_url, sessions, revision_id=None):
        self.ping_url = ping_url
        self.release_url = release_url
        self.sessions_list = EditingSessionsList(sessions)
        self.revision_id = revision_id

    def get_context_data(self, parent_context):
        return {
            "ping_url": self.ping_url,
            "release_url": self.release_url,
            "sessions_list": self.sessions_list,
            "revision_id": self.revision_id,
        }


class EditingSessionsList(Component):
    template_name = "wagtailadmin/shared/editing_sessions/list.html"

    def __init__(self, sessions):
        self.sessions = sessions

    def get_context_data(self, parent_context):
        return {"sessions": self.sessions}
