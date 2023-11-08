import React, { useState, useEffect } from 'react';
import { getTemplatePattern } from 'storybook-django/src/react';

const description = `
Wagtail comes with a base icon set, which can be extended by site implementers.

Here is a list of all available icons, auto-generated from our SVG sprite.
`;

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
            // eslint-disable-next-line react/no-danger
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
  title: 'Foundation / Icons',
  parameters: {
    docs: {
      extractComponentDescription: () => description,
    },
  },
  argTypes: {
    color: {
      description: 'Only intended for demo purposes',
    },
  },
};

export const AllIcons = (args) => <IconsTable {...args} />;

AllIcons.args = {
  color: 'currentColor',
};
