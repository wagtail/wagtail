import React, { useState, useEffect } from 'react';
import { getTemplatePattern } from 'storybook-django/src/react';

/**
 * Displays all icons within our sprite.
 */
const IconsTable = ({ color }: { color: string }) => {
  const [template, setTemplate] = useState<string>('');

  useEffect(() => {
    getTemplatePattern(
      'wagtailadmin/shared/icon.html',
      { name: '__icon__' },
      {},
      (html) => setTemplate(html),
    );
  }, []);

  return (
    <table>
      <caption>All registered icons</caption>
      <thead>
        <tr>
          <th scope="col">Visual</th>
          <th scope="col">Name</th>
          <th scope="col">Usage</th>
        </tr>
      </thead>
      {window.WAGTAIL_ICONS.map((icon) => (
        <tr key={icon}>
          <td
            dangerouslySetInnerHTML={{
              __html: template
                .replace(/__icon__/g, icon)
                .replace(/<svg/, `<svg style="fill: ${color};"`),
            }}
          />
          <td>
            <code>{icon}</code>
          </td>
          <td>
            <code>{`{% icon name="${icon}" %}`}</code>
          </td>
        </tr>
      ))}
    </table>
  );
};

export default {
  argTypes: {
    color: {
      description: 'Only intended for demo purposes',
    },
  },
};

export const Icons = (args) => <IconsTable {...args} />;

Icons.args = {
  color: 'currentColor',
};
