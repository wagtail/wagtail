const domReady = () =>
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

/**
 * Loads sprite data from either Local Storage or via async fetch.
 * Ensures the sprite data is backed up when pulled in from API.
 */
export const initIconSprite = (
  spriteContainer: HTMLElement,
  spriteURL: string,
  revisionKey = 'wagtail:spriteRevision',
  dataKey = 'wagtail:spriteData',
): void => {
  const hasLocalStorage: boolean =
    'localStorage' in window && typeof window.localStorage !== 'undefined';

  const insert = (data: string | null) => {
    if (!spriteContainer || !data) return;

    domReady().then(() => {
      // eslint-disable-next-line no-param-reassign
      spriteContainer.innerHTML = data;
    });
  };

  if (hasLocalStorage && localStorage.getItem(revisionKey) === spriteURL) {
    const data = localStorage.getItem(dataKey);
    insert(data);
  }

  fetch(spriteURL)
    .then((response) => response.text())
    .then((data) => {
      insert(data);
      if (hasLocalStorage) {
        localStorage.setItem(dataKey, data);
        localStorage.setItem(revisionKey, spriteURL);
      }
    })
    .catch((error) => {
      // eslint-disable-next-line no-console
      console.error(`Error fetching ${spriteURL}. Error: ${error}`);
    });
};
