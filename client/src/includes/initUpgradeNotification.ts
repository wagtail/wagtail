import { VersionNumber, VersionDeltaType } from '../utils/version';

/**
 * Controls the upgrade notification component to request the latest version
 * of Wagtail and presents a message to the user if the current version
 * is out of date.
 *
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
const initUpgradeNotification = () => {
  const container = document.querySelector(
    '[data-upgrade-notification]',
  ) as HTMLElement;

  if (!container) return;

  const releasesUrl = 'https://releases.wagtail.io/latest.txt';
  const currentVersion = new VersionNumber(container.dataset.currentVersion);
  const showLTSOnly = container.hasAttribute('data-upgrade-lts-only');
  const upgradeVersion = container.querySelector('[data-upgrade-version]');
  const upgradeLink = container.querySelector('[data-upgrade-link]');

  fetch(releasesUrl, {
    referrerPolicy: 'strict-origin-when-cross-origin',
  })
    .then((response) => {
      if (response.status !== 200) {
        // eslint-disable-next-line no-console
        console.error(
          `Unexpected response from ${releasesUrl}. Status: ${response.status}`,
        );
        return false;
      }
      return response.json();
    })
    .then((payload) => {
      let data = payload;

      if (data && data.lts && showLTSOnly) {
        data = data.lts;
      }

      if (data && data.version) {
        const latestVersion = new VersionNumber(data.version);
        const versionDelta = currentVersion.howMuchBehind(latestVersion);

        let releaseNotesUrl = null;
        if (!versionDelta) {
          return;
        }
        if (
          versionDelta === VersionDeltaType.MAJOR ||
          versionDelta === VersionDeltaType.MINOR
        ) {
          releaseNotesUrl = data.minorUrl;
        } else {
          releaseNotesUrl = data.url;
        }

        if (upgradeVersion instanceof HTMLElement) {
          upgradeVersion.innerText = [data.version, showLTSOnly ? '(LTS)' : '']
            .join(' ')
            .trim();
        }

        if (upgradeLink instanceof HTMLElement) {
          upgradeLink.setAttribute('href', releaseNotesUrl || '');
        }

        container.style.display = '';
      }
    })
    .catch((err) => {
      // eslint-disable-next-line no-console
      console.error(`Error fetching ${releasesUrl}. Error: ${err}`);
    });
};

export { initUpgradeNotification };
