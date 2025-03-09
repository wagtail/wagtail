/**
 * Jest adapter and overrides to support Jest testing with Enzyme
 * and JSDom.
 * This will only be loaded in Jest tests, not in Storybook.
 */

import Enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

Enzyme.configure({
  adapter: new Adapter(),
});

/** Mock window.scrollTo as not provided via JSDom */
window.scrollTo = jest.fn();

/** Mock scrollIntoView on elements, this is not provided by JSDom */
Element.prototype.scrollIntoView = jest.fn();

/** Mock console.warn to filter out warnings from React due to Draftail legacy Component API usage.
 * Draftail/Draft-js is unlikely to support these and the warnings are not useful for unit test output.
 */
/* eslint-disable no-console */
const consoleWarnOriginal = console.warn;
console.warn = function filterWarnings(...args) {
  /* eslint-enable no-console */

  const [warning, component] = args;

  const legacyReactWarnings = [
    'Warning: componentWillMount has been renamed, and is not recommended for use.',
    'Warning: componentWillReceiveProps has been renamed, and is not recommended for use.',
    'Warning: componentWillUpdate has been renamed, and is not recommended for use.',
  ];

  const ignoredComponents = ['DraftEditor', 'PluginEditor'];

  if (
    legacyReactWarnings.some((_) => warning.includes(_)) &&
    ignoredComponents.includes(component)
  ) {
    return;
  }

  consoleWarnOriginal.apply(console, args);
};
