import '../tests/stubs';

import '../../wagtail/admin/static_src/wagtailadmin/scss/core.scss';
import './preview.scss';

export const parameters = {
  controls: {
    hideNoControlsWarning: true,
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
};

const cachedIcons = sessionStorage.getItem('WAGTAIL_ICONS');
window.WAGTAIL_ICONS = cachedIcons ? JSON.parse(cachedIcons) : [];

/**
 * Loads Wagtail’s icon sprite into the DOM, similarly to the admin.
 */
const loadIconSprite = () => {
  const PATTERN_LIBRARY_SPRITE_URL = '/pattern-library/api/v1/sprite';

  window
    .fetch(PATTERN_LIBRARY_SPRITE_URL)
    .then((res) => res.text())
    .then((html) => {
      const sprite = document.createElement('div');
      sprite.innerHTML = html;
      const symbols = Array.from(sprite.querySelectorAll('symbol'));
      const icons = symbols.map((elt) => elt.id.replace('icon-', '')).sort();

      window.WAGTAIL_ICONS = icons;
      sessionStorage.setItem('WAGTAIL_ICONS', JSON.stringify(icons));

      if (document.body) {
        document.body.appendChild(sprite);
      } else {
        window.addEventListener('DOMContentLoaded', () => {
          document.body.appendChild(sprite);
        });
      }
    });
};

loadIconSprite();
