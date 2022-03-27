import React, { useState, useEffect } from 'react';
import { getTemplatePattern } from '../../../../../client/storybook/TemplatePattern';

/**
 * Displays all icons within our sprite.
 */
const Icons = ({ color }: { color: string }) => {
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
    <>
      {window.WAGTAIL_ICONS.map((icon) => (
        <div key={icon}>
          <span
            dangerouslySetInnerHTML={{
              __html: template
                .replace(/__icon__/g, icon)
                .replace(/<svg/, `<svg style="fill: ${color};"`),
            }}
          />
          <code>{`{% icon name="${icon}" %}`}</code>
        </div>
      ))}
    </>
  );
};

export default {
  argTypes: {
    color: {
      description: 'Only intended for demo purposes',
    },
  },
};

export const icons = (args) => <Icons {...args} />;

icons.args = {
  color: 'currentColor',
};
