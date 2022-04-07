import React from 'react';
import { fontFamily, typeScale } from './typography';

const description = `
Wagtail’s type styles are structured as design tokens, available as CSS classes.
`;

export default {
  title: 'Foundation / Typography',
  parameters: {
    docs: {
      extractComponentDescription: () => description,
    },
  },
};

export const FontFamilies = () => (
  <div>
    <p>Wagtail’s UI font is a system font stack:</p>
    <pre>{fontFamily.sans.join(', ')}</pre>
  </div>
);

export const TypeScale = () => (
  <table>
    <caption>All text styles</caption>
    <thead>
      <tr>
        <th scope="col">Style</th>
        <th scope="col">Class</th>
      </tr>
    </thead>
    <tbody>
      {Object.keys(typeScale).map((textStyle) => (
        <tr key={textStyle}>
          <td>
            <span className={`${textStyle} w-mt-4`}>
              {textStyle.replace('w-', '')}
            </span>
          </td>
          <td>
            <code>{`.${textStyle}`}</code>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
);
