// eslint-disable-next-line consistent-return
export const initIconSprite = (
  spriteContainer: HTMLElement,
  spriteURL: string,
) => {
  const revisionKey = 'wagtail:spriteRevision';
  const dataKey = 'wagtail:spriteData';
  const isLocalStorage: boolean =
    'localStorage' in window && typeof window.localStorage !== 'undefined';
  const insertIt = (data: string) => {
    if (spriteContainer) {
      // eslint-disable-next-line no-param-reassign
      spriteContainer.innerHTML = data;
    }
  };

  const insert = (data: string) => {
    if (document.body) {
      insertIt(data);
    } else {
      document.addEventListener('DOMContentLoaded', () => insertIt(data));
    }
  };

  if (isLocalStorage && localStorage.getItem(revisionKey) === spriteURL) {
    const data = localStorage.getItem(dataKey);
    if (data) {
      insert(data);
      return true;
    }
  }

  try {
    const request = new XMLHttpRequest();
    request.open('GET', spriteURL, true);
    request.onload = () => {
      if (request.status >= 200 && request.status < 400) {
        const data = request.responseText;
        insert(data);
        if (isLocalStorage) {
          localStorage.setItem(dataKey, data);
          localStorage.setItem(revisionKey, spriteURL);
        }
      }
    };
    request.send();
  } catch (e) {
    // eslint-disable-next-line no-console
    console.error(e);
  }
};
