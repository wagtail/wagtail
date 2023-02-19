/**
 * Returns a promise that resolves once the DOM is ready for interaction.
 */
const domReady = async () =>
  new Promise<void>((resolve) => {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => resolve(), {
        once: true,
        passive: true,
      });
    } else {
      resolve();
    }
  });

export { domReady };
