const { staticColors, transparencies } = require('./colors');
const colorThemes = require('./colorThemes');
const {
  generateColorVariables,
  generateThemeColorVariables,
} = require('./colorVariables');

describe('generateColorVariables', () => {
  it('generates all variables', () => {
    const colorVariables = generateColorVariables(staticColors);
    const generatedVariables = Object.keys(colorVariables);
    Object.values(staticColors).forEach((hues) => {
      Object.values(hues).forEach((shade) => {
        expect(generatedVariables).toContain(shade.cssVariable);
      });
    });
  });

  /**
   * If this test breaks, it means we’ve either changed our color palette, or changed how we make each of the colors customizable.
   * If the change is intentional, we will then need to update our `custom_user_interface_colors` documentation.
   * - Open Storybook’s color customization story in a browser
   * - Use your browser’s DevTools to copy the relevant story markup to our Markdown documentation.
   * - Leave the copied content exactly as-is when pasting, to avoid any Markdown formatting issues.
   */
  it('is stable (update custom_user_interface_colors documentation when this changes)', () => {
    const colorVariables = generateColorVariables(staticColors);
    expect(colorVariables).toMatchInlineSnapshot(`
      {
        "--w-color-black": "hsl(var(--w-color-black-hue) var(--w-color-black-saturation) var(--w-color-black-lightness))",
        "--w-color-black-hue": "0",
        "--w-color-black-lightness": "0%",
        "--w-color-black-saturation": "0%",
        "--w-color-critical-100": "hsl(var(--w-color-critical-100-hue) var(--w-color-critical-100-saturation) var(--w-color-critical-100-lightness))",
        "--w-color-critical-100-hue": "calc(var(--w-color-critical-200-hue) + 354.9)",
        "--w-color-critical-100-lightness": "calc(var(--w-color-critical-200-lightness) + 15.5%)",
        "--w-color-critical-100-saturation": "calc(var(--w-color-critical-200-saturation) + 40.2%)",
        "--w-color-critical-200": "hsl(var(--w-color-critical-200-hue) var(--w-color-critical-200-saturation) var(--w-color-critical-200-lightness))",
        "--w-color-critical-200-hue": "0",
        "--w-color-critical-200-lightness": "51.2%",
        "--w-color-critical-200-saturation": "57.4%",
        "--w-color-critical-50": "hsl(var(--w-color-critical-50-hue) var(--w-color-critical-50-saturation) var(--w-color-critical-50-lightness))",
        "--w-color-critical-50-hue": "var(--w-color-critical-200-hue)",
        "--w-color-critical-50-lightness": "calc(var(--w-color-critical-200-lightness) + 45.7%)",
        "--w-color-critical-50-saturation": "calc(var(--w-color-critical-200-saturation) + 30.1%)",
        "--w-color-grey-100": "hsl(var(--w-color-grey-100-hue) var(--w-color-grey-100-saturation) var(--w-color-grey-100-lightness))",
        "--w-color-grey-100-hue": "var(--w-color-grey-800-hue)",
        "--w-color-grey-100-lightness": "calc(var(--w-color-grey-800-lightness) + 76.4%)",
        "--w-color-grey-100-saturation": "var(--w-color-grey-800-saturation)",
        "--w-color-grey-150": "hsl(var(--w-color-grey-150-hue) var(--w-color-grey-150-saturation) var(--w-color-grey-150-lightness))",
        "--w-color-grey-150-hue": "var(--w-color-grey-800-hue)",
        "--w-color-grey-150-lightness": "calc(var(--w-color-grey-800-lightness) + 67%)",
        "--w-color-grey-150-saturation": "var(--w-color-grey-800-saturation)",
        "--w-color-grey-200": "hsl(var(--w-color-grey-200-hue) var(--w-color-grey-200-saturation) var(--w-color-grey-200-lightness))",
        "--w-color-grey-200-hue": "var(--w-color-grey-800-hue)",
        "--w-color-grey-200-lightness": "calc(var(--w-color-grey-800-lightness) + 45.9%)",
        "--w-color-grey-200-saturation": "var(--w-color-grey-800-saturation)",
        "--w-color-grey-400": "hsl(var(--w-color-grey-400-hue) var(--w-color-grey-400-saturation) var(--w-color-grey-400-lightness))",
        "--w-color-grey-400-hue": "var(--w-color-grey-800-hue)",
        "--w-color-grey-400-lightness": "calc(var(--w-color-grey-800-lightness) + 24.7%)",
        "--w-color-grey-400-saturation": "var(--w-color-grey-800-saturation)",
        "--w-color-grey-50": "hsl(var(--w-color-grey-50-hue) var(--w-color-grey-50-saturation) var(--w-color-grey-50-lightness))",
        "--w-color-grey-50-hue": "calc(var(--w-color-grey-800-hue) + 240)",
        "--w-color-grey-50-lightness": "calc(var(--w-color-grey-800-lightness) + 85.5%)",
        "--w-color-grey-50-saturation": "calc(var(--w-color-grey-800-saturation) + 12.5%)",
        "--w-color-grey-500": "hsl(var(--w-color-grey-500-hue) var(--w-color-grey-500-saturation) var(--w-color-grey-500-lightness))",
        "--w-color-grey-500-hue": "var(--w-color-grey-800-hue)",
        "--w-color-grey-500-lightness": "calc(var(--w-color-grey-800-lightness) + 8.6%)",
        "--w-color-grey-500-saturation": "var(--w-color-grey-800-saturation)",
        "--w-color-grey-600": "hsl(var(--w-color-grey-600-hue) var(--w-color-grey-600-saturation) var(--w-color-grey-600-lightness))",
        "--w-color-grey-600-hue": "var(--w-color-grey-800-hue)",
        "--w-color-grey-600-lightness": "calc(var(--w-color-grey-800-lightness) + 3.5%)",
        "--w-color-grey-600-saturation": "var(--w-color-grey-800-saturation)",
        "--w-color-grey-700": "hsl(var(--w-color-grey-700-hue) var(--w-color-grey-700-saturation) var(--w-color-grey-700-lightness))",
        "--w-color-grey-700-hue": "var(--w-color-grey-800-hue)",
        "--w-color-grey-700-lightness": "calc(var(--w-color-grey-800-lightness) + 1.9%)",
        "--w-color-grey-700-saturation": "var(--w-color-grey-800-saturation)",
        "--w-color-grey-800": "hsl(var(--w-color-grey-800-hue) var(--w-color-grey-800-saturation) var(--w-color-grey-800-lightness))",
        "--w-color-grey-800-hue": "0",
        "--w-color-grey-800-lightness": "11.4%",
        "--w-color-grey-800-saturation": "0%",
        "--w-color-info-100": "hsl(var(--w-color-info-100-hue) var(--w-color-info-100-saturation) var(--w-color-info-100-lightness))",
        "--w-color-info-100-hue": "calc(var(--w-color-info-125-hue) - 0.1)",
        "--w-color-info-100-lightness": "calc(var(--w-color-info-125-lightness) + 6.5%)",
        "--w-color-info-100-saturation": "calc(var(--w-color-info-125-saturation) + 0.7%)",
        "--w-color-info-125": "hsl(var(--w-color-info-125-hue) var(--w-color-info-125-saturation) var(--w-color-info-125-lightness))",
        "--w-color-info-125-hue": "194.0",
        "--w-color-info-125-lightness": "27.8%",
        "--w-color-info-125-saturation": "66.2%",
        "--w-color-info-50": "hsl(var(--w-color-info-50-hue) var(--w-color-info-50-saturation) var(--w-color-info-50-lightness))",
        "--w-color-info-50-hue": "calc(var(--w-color-info-125-hue) + 2.2)",
        "--w-color-info-50-lightness": "calc(var(--w-color-info-125-lightness) + 65.9%)",
        "--w-color-info-50-saturation": "calc(var(--w-color-info-125-saturation) + 15.1%)",
        "--w-color-info-75": "hsl(var(--w-color-info-75-hue) var(--w-color-info-75-saturation) var(--w-color-info-75-lightness))",
        "--w-color-info-75-hue": "calc(var(--w-color-info-125-hue) + 0.4)",
        "--w-color-info-75-lightness": "calc(var(--w-color-info-125-lightness) + 36.3%)",
        "--w-color-info-75-saturation": "calc(var(--w-color-info-125-saturation) - 27.4%)",
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
        "--w-color-warning-75": "hsl(var(--w-color-warning-75-hue) var(--w-color-warning-75-saturation) var(--w-color-warning-75-lightness))",
        "--w-color-warning-75-hue": "calc(var(--w-color-warning-100-hue) + 0.7)",
        "--w-color-warning-75-lightness": "calc(var(--w-color-warning-100-lightness) + 23.4%)",
        "--w-color-warning-75-saturation": "calc(var(--w-color-warning-100-saturation) - 2.8%)",
        "--w-color-white": "hsl(var(--w-color-white-hue) var(--w-color-white-saturation) var(--w-color-white-lightness))",
        "--w-color-white-hue": "0",
        "--w-color-white-lightness": "100%",
        "--w-color-white-saturation": "0%",
      }
    `);
  });
});

describe('transparencies', () => {
  it('is stable (update custom_user_interface_colors documentation when this changes)', () => {
    expect(transparencies).toMatchInlineSnapshot(`
      {
        "--w-color-black-10": "rgba(0, 0, 0, 0.10)",
        "--w-color-black-20": "rgba(0, 0, 0, 0.20)",
        "--w-color-black-25": "rgba(0, 0, 0, 0.25)",
        "--w-color-black-35": "rgba(0, 0, 0, 0.35)",
        "--w-color-black-5": "rgba(0, 0, 0, 0.05)",
        "--w-color-black-50": "rgba(0, 0, 0, 0.50)",
        "--w-color-white-10": "rgba(255, 255, 255, 0.10)",
        "--w-color-white-15": "rgba(255, 255, 255, 0.15)",
        "--w-color-white-50": "rgba(255, 255, 255, 0.50)",
        "--w-color-white-80": "rgba(255, 255, 255, 0.80)",
      }
    `);
  });
});

describe('generateThemeColorVariables', () => {
  it('uses the same variables in both themes', () => {
    const light = Object.keys(generateThemeColorVariables(colorThemes.light));
    const dark = Object.keys(generateThemeColorVariables(colorThemes.dark));
    expect(light).toEqual(dark);
  });

  it('uses color variables for all values (except focus)', () => {
    const values = [
      ...Object.values(generateThemeColorVariables(colorThemes.light)),
      ...Object.values(generateThemeColorVariables(colorThemes.dark)),
    ];
    expect(values.filter((val) => !val.startsWith('var('))).toEqual([
      '#00A885',
      '#00A885',
    ]);
  });

  it('light theme is stable (update custom_user_interface_colors documentation when this changes)', () => {
    expect(generateThemeColorVariables(colorThemes.light))
      .toMatchInlineSnapshot(`
      {
        "--w-color-border-button-outline-default": "var(--w-color-secondary)",
        "--w-color-border-button-outline-hover": "var(--w-color-secondary-400)",
        "--w-color-border-button-small-outline-default": "var(--w-color-grey-150)",
        "--w-color-border-field-default": "var(--w-color-grey-150)",
        "--w-color-border-field-hover": "var(--w-color-grey-200)",
        "--w-color-border-field-inactive": "var(--w-color-grey-150)",
        "--w-color-border-furniture": "var(--w-color-grey-100)",
        "--w-color-border-furniture-more-contrast": "var(--w-color-grey-200)",
        "--w-color-border-interactive-more-contrast": "var(--w-color-grey-500)",
        "--w-color-border-interactive-more-contrast-dark-bg": "var(--w-color-grey-150)",
        "--w-color-border-interactive-more-contrast-dark-bg-hover": "var(--w-color-white)",
        "--w-color-border-interactive-more-contrast-hover": "var(--w-color-black)",
        "--w-color-box-shadow-md": "var(--w-color-black-25)",
        "--w-color-focus": "#00A885",
        "--w-color-icon-primary": "var(--w-color-primary)",
        "--w-color-icon-primary-hover": "var(--w-color-primary-200)",
        "--w-color-icon-secondary": "var(--w-color-grey-400)",
        "--w-color-icon-secondary-hover": "var(--w-color-primary-200)",
        "--w-color-surface-button-critical-hover": "var(--w-color-critical-50)",
        "--w-color-surface-button-default": "var(--w-color-secondary)",
        "--w-color-surface-button-hover": "var(--w-color-secondary-400)",
        "--w-color-surface-button-inactive": "var(--w-color-grey-400)",
        "--w-color-surface-button-outline-hover": "var(--w-color-secondary-50)",
        "--w-color-surface-dashboard-panel": "var(--w-color-white)",
        "--w-color-surface-field": "var(--w-color-white)",
        "--w-color-surface-field-inactive": "var(--w-color-grey-50)",
        "--w-color-surface-header": "var(--w-color-grey-50)",
        "--w-color-surface-info-panel": "var(--w-color-info-50)",
        "--w-color-surface-menu-item-active": "var(--w-color-primary-200)",
        "--w-color-surface-menus": "var(--w-color-primary)",
        "--w-color-surface-page": "var(--w-color-white)",
        "--w-color-surface-status-label": "var(--w-color-info-50)",
        "--w-color-surface-tooltip": "var(--w-color-primary-200)",
        "--w-color-text-button": "var(--w-color-white)",
        "--w-color-text-button-critical-outline-hover": "var(--w-color-critical-200)",
        "--w-color-text-button-outline-default": "var(--w-color-secondary)",
        "--w-color-text-button-outline-hover": "var(--w-color-secondary-400)",
        "--w-color-text-context": "var(--w-color-grey-600)",
        "--w-color-text-error": "var(--w-color-critical-200)",
        "--w-color-text-highlight": "var(--w-color-secondary-75)",
        "--w-color-text-label": "var(--w-color-primary)",
        "--w-color-text-label-menus-active": "var(--w-color-white)",
        "--w-color-text-label-menus-default": "var(--w-color-white-80)",
        "--w-color-text-link-default": "var(--w-color-secondary)",
        "--w-color-text-link-hover": "var(--w-color-secondary-400)",
        "--w-color-text-link-info": "var(--w-color-secondary-400)",
        "--w-color-text-meta": "var(--w-color-grey-400)",
        "--w-color-text-placeholder": "var(--w-color-grey-400)",
        "--w-color-text-status-label": "var(--w-color-info-100)",
      }
    `);
  });

  it('dark theme is stable (update custom_user_interface_colors documentation when this changes)', () => {
    expect(generateThemeColorVariables(colorThemes.dark))
      .toMatchInlineSnapshot(`
      {
        "--w-color-border-button-outline-default": "var(--w-color-secondary-100)",
        "--w-color-border-button-outline-hover": "var(--w-color-secondary-100)",
        "--w-color-border-button-small-outline-default": "var(--w-color-grey-400)",
        "--w-color-border-field-default": "var(--w-color-grey-400)",
        "--w-color-border-field-hover": "var(--w-color-grey-200)",
        "--w-color-border-field-inactive": "var(--w-color-grey-500)",
        "--w-color-border-furniture": "var(--w-color-grey-500)",
        "--w-color-border-furniture-more-contrast": "var(--w-color-grey-400)",
        "--w-color-border-interactive-more-contrast": "var(--w-color-grey-150)",
        "--w-color-border-interactive-more-contrast-dark-bg": "var(--w-color-grey-150)",
        "--w-color-border-interactive-more-contrast-dark-bg-hover": "var(--w-color-white)",
        "--w-color-border-interactive-more-contrast-hover": "var(--w-color-white)",
        "--w-color-box-shadow-md": "var(--w-color-black-50)",
        "--w-color-focus": "#00A885",
        "--w-color-icon-primary": "var(--w-color-grey-150)",
        "--w-color-icon-primary-hover": "var(--w-color-grey-50)",
        "--w-color-icon-secondary": "var(--w-color-grey-150)",
        "--w-color-icon-secondary-hover": "var(--w-color-grey-50)",
        "--w-color-surface-button-critical-hover": "var(--w-color-grey-600)",
        "--w-color-surface-button-default": "var(--w-color-secondary)",
        "--w-color-surface-button-hover": "var(--w-color-secondary-400)",
        "--w-color-surface-button-inactive": "var(--w-color-grey-400)",
        "--w-color-surface-button-outline-hover": "var(--w-color-grey-700)",
        "--w-color-surface-dashboard-panel": "var(--w-color-grey-800)",
        "--w-color-surface-field": "var(--w-color-grey-600)",
        "--w-color-surface-field-inactive": "var(--w-color-grey-500)",
        "--w-color-surface-header": "var(--w-color-grey-700)",
        "--w-color-surface-info-panel": "var(--w-color-info-100)",
        "--w-color-surface-menu-item-active": "var(--w-color-grey-700)",
        "--w-color-surface-menus": "var(--w-color-grey-800)",
        "--w-color-surface-page": "var(--w-color-grey-600)",
        "--w-color-surface-status-label": "var(--w-color-grey-600)",
        "--w-color-surface-tooltip": "var(--w-color-grey-500)",
        "--w-color-text-button": "var(--w-color-white)",
        "--w-color-text-button-critical-outline-hover": "var(--w-color-critical-50)",
        "--w-color-text-button-outline-default": "var(--w-color-secondary-100)",
        "--w-color-text-button-outline-hover": "var(--w-color-secondary-100)",
        "--w-color-text-context": "var(--w-color-grey-50)",
        "--w-color-text-error": "var(--w-color-critical-100)",
        "--w-color-text-highlight": "var(--w-color-secondary-400)",
        "--w-color-text-label": "var(--w-color-grey-150)",
        "--w-color-text-label-menus-active": "var(--w-color-white)",
        "--w-color-text-label-menus-default": "var(--w-color-white-80)",
        "--w-color-text-link-default": "var(--w-color-secondary-100)",
        "--w-color-text-link-hover": "var(--w-color-secondary-75)",
        "--w-color-text-link-info": "var(--w-color-grey-50)",
        "--w-color-text-meta": "var(--w-color-grey-150)",
        "--w-color-text-placeholder": "var(--w-color-grey-200)",
        "--w-color-text-status-label": "var(--w-color-info-75)",
      }
    `);
  });
});
