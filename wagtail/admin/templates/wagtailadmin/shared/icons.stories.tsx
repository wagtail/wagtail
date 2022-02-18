import React, { useState, useEffect } from 'react';
import { renderPattern } from 'storybook-django';

const fetchIconTemplate = () =>
  renderPattern(
    window.PATTERN_LIBRARY_API,
    'wagtailadmin/shared/icon.html',
    {
      name: '__icon__',
    },
    {},
  ).then((res) => res.text());

/**
 * Displays all icons within our sprite.
 */
const Icons = () => {
  const [template, setTemplate] = useState<string>('');
  const [icons, setIcons] = useState<string[]>([]);

  useEffect(() => {
    const sprite = document.querySelector('[data-sprite]');
    if (sprite) {
      const symbols = Array.from(sprite.querySelectorAll('symbol'));
      setIcons(symbols.map((s) => s.id.replace('icon-', '')));
    }

    fetchIconTemplate().then((html) => setTemplate(html));
  }, []);

  return (
    <ul>
      {icons.map((icon) => (
        <li key={icon}>
          <span
            dangerouslySetInnerHTML={{
              __html: template.replace(/__icon__/g, icon),
            }}
          />
          <code>{`{% icon name="${icon}" %}`}</code>
        </li>
      ))}
    </ul>
  );
};

export default {
  title: 'Shared / Icons',
  component: Icons,
};

export const All = () => <Icons />;
