const colors = require('./colors');
const { generateColorVariables } = require('./colorVariables');

describe('generateColorVariables', () => {
  it('generates all variables', () => {
    const colorVariables = generateColorVariables(colors);
    const generatedVariables = Object.keys(colorVariables);
    Object.values(colors).forEach((hues) => {
      Object.values(hues).forEach((shade) => {
        expect(generatedVariables).toContain(shade.cssVariable);
      });
    });
  });

  /**
   * If this test breaks, it means we’ve either changed our color palette, or changed how we make each of the colors customisable.
   * If the change is intentional, we will then need to update our `custom_user_interface_colours` documentation.
   * - Open Storybook’s color customisation story in a browser
   * - Use your browser’s DevTools to copy the relevant story markup to our Markdown documentation.
   * - Leave the copied content exactly as-is when pasting, to avoid any Markdown formatting issues.
   */
  it('is stable (update custom_user_interface_colours documentation when this changes)', () => {
    const colorVariables = generateColorVariables(colors);
    expect(colorVariables).toMatchInlineSnapshot(`
      Object {
        "--w-color-black": "hsl(var(--w-color-black-hue) var(--w-color-black-saturation) var(--w-color-black-lightness))",
        "--w-color-black-hue": "0",
        "--w-color-black-lightness": "0%",
        "--w-color-black-saturation": "0%",
        "--w-color-critical-100": "hsl(var(--w-color-critical-100-hue) var(--w-color-critical-100-saturation) var(--w-color-critical-100-lightness))",
        "--w-color-critical-100-hue": "calc(var(--w-color-critical-200-hue) + 354.9)",
        "--w-color-critical-100-lightness": "calc(var(--w-color-critical-200-lightness) + 13.2%)",
        "--w-color-critical-100-saturation": "calc(var(--w-color-critical-200-saturation) + 39.8%)",
        "--w-color-critical-200": "hsl(var(--w-color-critical-200-hue) var(--w-color-critical-200-saturation) var(--w-color-critical-200-lightness))",
        "--w-color-critical-200-hue": "0",
        "--w-color-critical-200-lightness": "53.5%",
        "--w-color-critical-200-saturation": "57.8%",
        "--w-color-critical-50": "hsl(var(--w-color-critical-50-hue) var(--w-color-critical-50-saturation) var(--w-color-critical-50-lightness))",
        "--w-color-critical-50-hue": "var(--w-color-critical-200-hue)",
        "--w-color-critical-50-lightness": "calc(var(--w-color-critical-200-lightness) + 41.8%)",
        "--w-color-critical-50-saturation": "calc(var(--w-color-critical-200-saturation) + 25.5%)",
        "--w-color-grey-100": "hsl(var(--w-color-grey-100-hue) var(--w-color-grey-100-saturation) var(--w-color-grey-100-lightness))",
        "--w-color-grey-100-hue": "var(--w-color-grey-600-hue)",
        "--w-color-grey-100-lightness": "calc(var(--w-color-grey-600-lightness) + 72.9%)",
        "--w-color-grey-100-saturation": "var(--w-color-grey-600-saturation)",
        "--w-color-grey-150": "hsl(var(--w-color-grey-150-hue) var(--w-color-grey-150-saturation) var(--w-color-grey-150-lightness))",
        "--w-color-grey-150-hue": "var(--w-color-grey-600-hue)",
        "--w-color-grey-150-lightness": "calc(var(--w-color-grey-600-lightness) + 63.5%)",
        "--w-color-grey-150-saturation": "var(--w-color-grey-600-saturation)",
        "--w-color-grey-200": "hsl(var(--w-color-grey-200-hue) var(--w-color-grey-200-saturation) var(--w-color-grey-200-lightness))",
        "--w-color-grey-200-hue": "var(--w-color-grey-600-hue)",
        "--w-color-grey-200-lightness": "calc(var(--w-color-grey-600-lightness) + 42.4%)",
        "--w-color-grey-200-saturation": "var(--w-color-grey-600-saturation)",
        "--w-color-grey-400": "hsl(var(--w-color-grey-400-hue) var(--w-color-grey-400-saturation) var(--w-color-grey-400-lightness))",
        "--w-color-grey-400-hue": "var(--w-color-grey-600-hue)",
        "--w-color-grey-400-lightness": "calc(var(--w-color-grey-600-lightness) + 21.2%)",
        "--w-color-grey-400-saturation": "var(--w-color-grey-600-saturation)",
        "--w-color-grey-50": "hsl(var(--w-color-grey-50-hue) var(--w-color-grey-50-saturation) var(--w-color-grey-50-lightness))",
        "--w-color-grey-50-hue": "calc(var(--w-color-grey-600-hue) + 240)",
        "--w-color-grey-50-lightness": "calc(var(--w-color-grey-600-lightness) + 82%)",
        "--w-color-grey-50-saturation": "calc(var(--w-color-grey-600-saturation) + 12.5%)",
        "--w-color-grey-500": "hsl(var(--w-color-grey-500-hue) var(--w-color-grey-500-saturation) var(--w-color-grey-500-lightness))",
        "--w-color-grey-500-hue": "var(--w-color-grey-600-hue)",
        "--w-color-grey-500-lightness": "calc(var(--w-color-grey-600-lightness) + 5.1%)",
        "--w-color-grey-500-saturation": "var(--w-color-grey-600-saturation)",
        "--w-color-grey-600": "hsl(var(--w-color-grey-600-hue) var(--w-color-grey-600-saturation) var(--w-color-grey-600-lightness))",
        "--w-color-grey-600-hue": "0",
        "--w-color-grey-600-lightness": "14.9%",
        "--w-color-grey-600-saturation": "0%",
        "--w-color-info-100": "hsl(var(--w-color-info-100-hue) var(--w-color-info-100-saturation) var(--w-color-info-100-lightness))",
        "--w-color-info-100-hue": "193.7",
        "--w-color-info-100-lightness": "36.3%",
        "--w-color-info-100-saturation": "66.5%",
        "--w-color-info-50": "hsl(var(--w-color-info-50-hue) var(--w-color-info-50-saturation) var(--w-color-info-50-lightness))",
        "--w-color-info-50-hue": "calc(var(--w-color-info-100-hue) + 2.5)",
        "--w-color-info-50-lightness": "calc(var(--w-color-info-100-lightness) + 57.4%)",
        "--w-color-info-50-saturation": "calc(var(--w-color-info-100-saturation) + 14.8%)",
        "--w-color-positive-100": "hsl(var(--w-color-positive-100-hue) var(--w-color-positive-100-saturation) var(--w-color-positive-100-lightness))",
        "--w-color-positive-100-hue": "162.1",
        "--w-color-positive-100-lightness": "31.6%",
        "--w-color-positive-100-saturation": "66.5%",
        "--w-color-positive-50": "hsl(var(--w-color-positive-50-hue) var(--w-color-positive-50-saturation) var(--w-color-positive-50-lightness))",
        "--w-color-positive-50-hue": "calc(var(--w-color-positive-100-hue) + 2.3)",
        "--w-color-positive-50-lightness": "calc(var(--w-color-positive-100-lightness) + 61.5%)",
        "--w-color-positive-50-saturation": "calc(var(--w-color-positive-100-saturation) + 10.6%)",
        "--w-color-primary": "hsl(var(--w-color-primary-hue) var(--w-color-primary-saturation) var(--w-color-primary-lightness))",
        "--w-color-primary-200": "hsl(var(--w-color-primary-200-hue) var(--w-color-primary-200-saturation) var(--w-color-primary-200-lightness))",
        "--w-color-primary-200-hue": "calc(var(--w-color-primary-hue) - 0.5)",
        "--w-color-primary-200-lightness": "calc(var(--w-color-primary-lightness) - 4.1%)",
        "--w-color-primary-200-saturation": "calc(var(--w-color-primary-saturation) - 0.4%)",
        "--w-color-primary-hue": "254.3",
        "--w-color-primary-lightness": "24.5%",
        "--w-color-primary-saturation": "50.4%",
        "--w-color-secondary": "hsl(var(--w-color-secondary-hue) var(--w-color-secondary-saturation) var(--w-color-secondary-lightness))",
        "--w-color-secondary-100": "hsl(var(--w-color-secondary-100-hue) var(--w-color-secondary-100-saturation) var(--w-color-secondary-100-lightness))",
        "--w-color-secondary-100-hue": "calc(var(--w-color-secondary-hue) - 0.2)",
        "--w-color-secondary-100-lightness": "calc(var(--w-color-secondary-lightness) + 10%)",
        "--w-color-secondary-100-saturation": "var(--w-color-secondary-saturation)",
        "--w-color-secondary-400": "hsl(var(--w-color-secondary-400-hue) var(--w-color-secondary-400-saturation) var(--w-color-secondary-400-lightness))",
        "--w-color-secondary-400-hue": "calc(var(--w-color-secondary-hue) + 1.4)",
        "--w-color-secondary-400-lightness": "calc(var(--w-color-secondary-lightness) - 6.3%)",
        "--w-color-secondary-400-saturation": "var(--w-color-secondary-saturation)",
        "--w-color-secondary-50": "hsl(var(--w-color-secondary-50-hue) var(--w-color-secondary-50-saturation) var(--w-color-secondary-50-lightness))",
        "--w-color-secondary-50-hue": "calc(var(--w-color-secondary-hue) - 0.5)",
        "--w-color-secondary-50-lightness": "calc(var(--w-color-secondary-lightness) + 72.2%)",
        "--w-color-secondary-50-saturation": "calc(var(--w-color-secondary-saturation) - 37.5%)",
        "--w-color-secondary-600": "hsl(var(--w-color-secondary-600-hue) var(--w-color-secondary-600-saturation) var(--w-color-secondary-600-lightness))",
        "--w-color-secondary-600-hue": "calc(var(--w-color-secondary-hue) + 1.2)",
        "--w-color-secondary-600-lightness": "calc(var(--w-color-secondary-lightness) - 11.2%)",
        "--w-color-secondary-600-saturation": "var(--w-color-secondary-saturation)",
        "--w-color-secondary-75": "hsl(var(--w-color-secondary-75-hue) var(--w-color-secondary-75-saturation) var(--w-color-secondary-75-lightness))",
        "--w-color-secondary-75-hue": "calc(var(--w-color-secondary-hue) + 0.2)",
        "--w-color-secondary-75-lightness": "calc(var(--w-color-secondary-lightness) + 42.8%)",
        "--w-color-secondary-75-saturation": "calc(var(--w-color-secondary-saturation) - 47%)",
        "--w-color-secondary-hue": "180.5",
        "--w-color-secondary-lightness": "24.7%",
        "--w-color-secondary-saturation": "100%",
        "--w-color-warning-100": "hsl(var(--w-color-warning-100-hue) var(--w-color-warning-100-saturation) var(--w-color-warning-100-lightness))",
        "--w-color-warning-100-hue": "39.6",
        "--w-color-warning-100-lightness": "49%",
        "--w-color-warning-100-saturation": "100%",
        "--w-color-warning-50": "hsl(var(--w-color-warning-50-hue) var(--w-color-warning-50-saturation) var(--w-color-warning-50-lightness))",
        "--w-color-warning-50-hue": "calc(var(--w-color-warning-100-hue) - 2.3)",
        "--w-color-warning-50-lightness": "calc(var(--w-color-warning-100-lightness) + 41.8%)",
        "--w-color-warning-50-saturation": "calc(var(--w-color-warning-100-saturation) - 21.3%)",
        "--w-color-white": "hsl(var(--w-color-white-hue) var(--w-color-white-saturation) var(--w-color-white-lightness))",
        "--w-color-white-hue": "0",
        "--w-color-white-lightness": "100%",
        "--w-color-white-saturation": "0%",
      }
    `);
  });
});
