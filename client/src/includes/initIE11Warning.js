import { IS_IE11 } from '../config/wagtailConfig';

/**
 * Toggles IE11-only warning messages, if any.
 */
const initIE11Warning = () => {
  if (!IS_IE11) {
    return;
  }

  const warnings = [].slice.call(document.querySelectorAll('[data-ie11-warning]'));

  warnings.forEach(warning => {
    // eslint-disable-next-line no-param-reassign
    warning.hidden = false;
  });
};

export { initIE11Warning };
