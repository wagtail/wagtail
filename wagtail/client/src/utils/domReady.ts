/**
 * Returns a promise that resolves once the DOM is ready for interaction.
 */
const domReady = async () => {
  if (document.readyState !== 'loading') return;
  await new Promise<void>((resolve) => {
    document.addEventListener('DOMContentLoaded', () => resolve(), {
      once: true,
      passive: true,
    });
  });
};

export { domReady };
