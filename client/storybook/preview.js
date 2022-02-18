import '../tests/stubs';

import '../../wagtail/admin/static_src/wagtailadmin/scss/core.scss';
import '../../wagtail/admin/static_src/wagtailadmin/scss/sidebar.scss';

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
};
