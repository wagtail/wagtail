import React from 'react';
import colors, { Hues, Shade } from './colors';

const description = `
Wagtail’s typographic styles are made available as separate design tokens, but in most scenarios it’s better to use one of the predefined text styles.
`;

interface PaletteProps {
  color: string;
  hues: Hues;
}

/**
 * Generates a contrast grid URL from our color palette.
 */
const getContrastGridLink = () => {
  const url = 'https://contrast-grid.eightshapes.com/';
  const parameters =
    '?version=1.1.0&es-color-form__tile-size=compact&es-color-form__show-contrast=aaa&es-color-form__show-contrast=aa&es-color-form__show-contrast=aa18';
  const bg = [];
  const fg = [];
  Object.values(colors).forEach((hues: Hues) => {
    Object.values(hues).forEach((shade: Shade) => {
      const color = `${shade.hex}, ${shade.textUtility.replace('w-text-', '')}`;
      bg.push(color);

      if (!shade.usage.toLowerCase().includes('background only')) {
        fg.push(color);
      }
    });
  });

  return `${url}${parameters}&background-colors=${encodeURIComponent(
    bg.join('\r\n'),
  )}&foreground-colors=${encodeURIComponent(fg.join('\r\n'))}`;
};

const Palette = ({ color, hues }: PaletteProps) => (
  <div className="w-mb-4 w-mr-4 w-flex w-flex-row">
    {Object.entries(hues).map(([name, shade]) => (
      <div key={name}>
        <h3 className="w-h3">{`${color} ${name === 'DEFAULT' ? '' : name}`}</h3>
        <div
          className={`w-p-3 w-flex w-flex-col w-w-40 w-h-40 ${
            shade.bgUtility
          } ${
            color === 'white' ? 'w-border w-border-solid w-border-grey-600' : ''
          } w-text-14 w-text-${shade.contrastText}`}
        >
          <code>{shade.textUtility}</code>
          <code>{shade.bgUtility}</code>
          <code>{shade.hex}</code>
        </div>
        <p className="mt-3 w-w-40">{shade.usage}</p>
      </div>
    ))}
  </div>
);

export default {
  title: 'Foundation / Colors',
  parameters: {
    docs: {
      extractComponentDescription: () => description,
    },
  },
};

export const ColorPalette = () => (
  <>
    <p>
      View <a href={getContrastGridLink()}>Contrast Grid</a>. Here is our full
      color palette, with contrasting text chosen for readability of this
      example only.
    </p>
    {Object.entries(colors).map(([color, hues]) => (
      <div key={color}>
        <h2 className="w-sr-only">{color}</h2>
        <Palette color={color} hues={hues} />
      </div>
    ))}
  </>
);
