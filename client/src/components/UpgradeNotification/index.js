import { versionOutOfDate } from '../../utils/version';

const initUpgradeNotification = () => {
  const container = document.querySelector('[data-upgrade]');

  if (!container) {
    return;
  }

  /*
  *   Expected JSON payload:
  *   {
  *       "version" : "1.2.3",    // Version number. Can only contain numbers and decimal point.
  *       "url" : "https://wagtail.io"  // Absolute URL to page/file containing release notes or actual package. It's up to you.
  *   }
  */
  const releasesUrl = 'https://releases.wagtail.io/latest.txt';
  const currentVersion = container.dataset.wagtailVersion;

  fetch(releasesUrl).then(response => {
    if (response.status !== 200) {
      // eslint-disable-next-line no-console
      console.log(`Unexpected response from ${releasesUrl}. Status: ${response.status}`);
      return false;
    }
    return response.json();
  }).then(data => {
    if (data && data.version && versionOutOfDate(data.version, currentVersion)) {
      container.querySelector('[data-upgrade-version]').innerText = data.version;
      container.querySelector('[data-upgrade-link]').setAttribute('href', data.url);
      container.style.display = '';
    }
  })
    .catch(err => {
      // eslint-disable-next-line no-console
      console.log(`Error fetching ${releasesUrl}. Error: ${err}`);
    });
};

export { initUpgradeNotification };
