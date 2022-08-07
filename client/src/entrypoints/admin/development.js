/**
 * The purpose of this entrypoint is to add code that can be run when working
 * with Django on DEBUG mode.
 * This is intentionally mean to run even for production builds of the JS itself
 * but provide those building on Wagtail to get some helpful warnings.
 */

/* eslint-disable no-console */
// see client/src/utils/deprecation.ts - enable client-side debug

console.info('Wagtail developer debug mode enabled');

/**
 * Listen to any development warning events and log them to the console as
 * a warning with the detail added to the message.
 */
document.addEventListener('wagtail:development-warning', ({ detail, target }) =>
  console.warn(
    ...[...Object.values(detail), target !== document && target].filter(
      Boolean,
    ),
  ),
);
