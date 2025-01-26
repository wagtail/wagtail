/**
 * Generate a CSS calc() expression so one HSL component is derived from another.
 * For example, with a reference color of `hsl(66 50% 25%)`, and a derived color of hsl(66 65% 20%),
 * - The hue components are identical, so the derived hue should just refer to the reference hue.
 * - Saturation for the derived color is higher, so should be `calc(var(--ref-saturation) + 15%)`
 * - Lightness for the derived color is lower, so should be `calc(var(--ref-lightness) - 5%)`.
 */
const calcHSLDifference = (refVariable, refValue, value, unit = '') => {
  const ref = Number(refValue);
  const val = Number(value);

  // If the value is equal to the reference, there is nothing to calc.
  if (ref === val) {
    return `var(${refVariable})`;
  }

  // Either add or remove the difference based on whether it’s positive or negative.
  const diff = (ref * 10 - val * 10) / 10;
  const operation = `${diff > 0 ? '-' : '+'} ${Math.abs(diff)}${unit}`;

  return `calc(var(${refVariable}) ${operation})`;
};

/**
 * Generate customizable CSS variables for a color palette, with override-able HSL components.
 *
 * For each shade of a color, we want to generate four variables:
 * - One for each HSL component of the color (Hue, Saturation, Lightness).
 * - A valid HSL color value combining the three components.
 *
 * A shade’s HSL components need to be derived from the reference color’s HSL components,
 * so site implementers can change all shades of a color at once by setting the HSL components of the "reference" color.
 *
 * For example, for a "light red" color derived from "red", this will create:
 * --red-light-hue: var(--red-hue);
 * --red-light-saturation: var(--red-saturation + 15%);
 * --red-light-lightness: calc(var(--red-lightness) - 5%);
 * --red-light: hsl(var(--red-light-hue) var(--red-light-saturation) var(--red-light-lightness));
 *
 * For the red reference color defined as `hsl(66 50% 25%)`, this will create:
 * --red-hue: 66;
 * --red-saturation: 50%;
 * --red-lightness: 25%;
 * --red: hsl(var(--red-hue) var(--red-saturation) var(--red-lightness));
 *
 */
const generateColorVariables = (colors) => {
  /* eslint-disable no-param-reassign, id-length */
  const colorVariables = Object.values(colors).reduce((root, hues) => {
    // Use the DEFAULT hue as a reference to derive others from, or the darkest if there is no defined default.
    const darkestHue = Object.keys(hues).sort((a, b) => b - a)[0];
    const reference = hues.DEFAULT || hues[darkestHue];
    const [refH, refS, refL] = reference.hsl.match(/\d+(\.\d+)?/g);
    const refVar = reference.cssVariable;

    // Generate color variables for all individual color shades, based on the reference.
    Object.values(hues).forEach((shade) => {
      // CSS variables will we generate.
      const vars = {
        hsl: shade.cssVariable,
        h: `${shade.cssVariable}-hue`,
        s: `${shade.cssVariable}-saturation`,
        l: `${shade.cssVariable}-lightness`,
      };
      const [h, s, l] = shade.hsl.match(/\d+(\.\d+)?/g);
      const isReferenceShade = reference.hex === shade.hex;

      if (isReferenceShade) {
        // If this is the reference shade, we use its HSL values as-is.
        root[vars.h] = h;
        root[vars.s] = `${s}%`;
        root[vars.l] = `${l}%`;
      } else {
        // If this is a derived shade, we will derive its HSL values from the reference.
        root[vars.h] = calcHSLDifference(`${refVar}-hue`, refH, h);
        root[vars.s] = calcHSLDifference(`${refVar}-saturation`, refS, s, '%');
        root[vars.l] = calcHSLDifference(`${refVar}-lightness`, refL, l, '%');
      }

      root[vars.hsl] = `hsl(var(${vars.h}) var(${vars.s}) var(${vars.l}))`;
    });

    return root;
  }, {});
  return colorVariables;
};

const generateThemeColorVariables = (themeCategories) => {
  const colorVariables = {};

  themeCategories.forEach((category) => {
    Object.values(category.tokens).forEach((token) => {
      colorVariables[token.cssVariable] = token.value;
    });
  });

  return colorVariables;
};

module.exports = {
  generateColorVariables,
  generateThemeColorVariables,
};
