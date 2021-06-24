export class SidebarPreferencesDefinition {
    collapsed: boolean;
    preferencesUrl: string;

    constructor({ collapsed, preferencesUrl }) {
      this.collapsed = collapsed;
      this.preferencesUrl = preferencesUrl;
    }
}

type UpdatableSidebarPreferences = {
  collapsed: boolean;
}

export class SidebarPreferences extends SidebarPreferencesDefinition {
  getCSRFToken = (): string => wagtailConfig.CSRF_TOKEN;

  update = (prefs: UpdatableSidebarPreferences): void => {
    const fetch = global.fetch;

    fetch(this.preferencesUrl, {
      method: 'POST',
      credentials: 'include',
      mode: 'same-origin',
      headers: {
        'X-CSRFToken': this.getCSRFToken(),
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(prefs),
    });
  };
}
