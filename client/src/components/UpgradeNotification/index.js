import { VersionNumber, VersionDeltaType } from '../../utils/version';

const initUpgradeNotification = () => {
  const container = document.querySelector('[data-upgrade]');

  if (!container) {
    return;
  }

  /*
   * Expected JSON payload:
   *
   * {
   *     "version": "2.15.2",
   *     "url":     "https://docs.wagtail.io/en/stable/releases/2.15.2.html",
   *     "minorUrl": "https://docs.wagtail.io/en/stable/releases/2.15.html",
   *     "lts": {
   *         "version": "2.12.8",
   *         "url": "https://docs.wagtail.io/en/stable/releases/2.12.8.html",
   *         "minorUrl": "https://docs.wagtail.io/en/stable/releases/2.12.html"
   *     }
   * }
   */
  const releasesUrl = 'https://releases.wagtail.io/latest.txt';
  const currentVersion = new VersionNumber(container.dataset.wagtailVersion);

  fetch(releasesUrl)
    .then((response) => {
      if (response.status !== 200) {
        // eslint-disable-next-line no-console
        console.log(
          `Unexpected response from ${releasesUrl}. Status: ${response.status}`,
        );
        return false;
      }
      return response.json();
    })
    .then((data) => {
      if (data && data.version) {
        const latestVersion = new VersionNumber(data.version);
        const versionDelta = currentVersion.howMuchBehind(latestVersion);

        let releaseNotesUrl = undefined;
        if (!versionDelta) {
          return;
        } else if (
          versionDelta === VersionDeltaType.MAJOR ||
          versionDelta === VersionDeltaType.MINOR
        ) {
          releaseNotesUrl = data.minorUrl;
        } else {
          releaseNotesUrl = data.url;
        }

        container.querySelector('[data-upgrade-version]').innerText =
          data.version;
        container
          .querySelector('[data-upgrade-link]')
          .setAttribute('href', releaseNotesUrl);
        container.style.display = '';
      }
    })
    .catch((err) => {
      // eslint-disable-next-line no-console
      console.log(`Error fetching ${releasesUrl}. Error: ${err}`);
    });
};

export { initUpgradeNotification };
