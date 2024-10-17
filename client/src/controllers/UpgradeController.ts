import { Controller } from '@hotwired/stimulus';
import { VersionNumber, VersionDeltaType } from '../utils/version';

interface VersionData {
  version: string;
  url: string;
  minorUrl: string;
}

interface LatestVersionData extends VersionData {
  lts: VersionData;
}

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
export class UpgradeController extends Controller<HTMLElement> {
  static targets = ['latestVersion', 'link'];
  static values = {
    currentVersion: String,
    ltsOnly: { default: false, type: Boolean },
    url: { default: 'https://releases.wagtail.org/latest.txt', type: String },
  };

  declare readonly hasLatestVersionTarget: boolean;
  declare readonly hasLinkTarget: boolean;
  declare currentVersionValue: string;
  declare latestVersionTarget: HTMLElement;
  declare linkTarget: HTMLElement;
  declare ltsOnlyValue: any;
  declare urlValue: string;

  connect() {
    this.checkVersion();
  }

  checkVersion() {
    const releasesUrl = this.urlValue;
    const currentVersion = new VersionNumber(this.currentVersionValue);
    const showLTSOnly = this.ltsOnlyValue;
    fetch(releasesUrl, {
      referrerPolicy: 'strict-origin-when-cross-origin',
    })
      .then((response) => {
        if (response.status !== 200) {
          throw Error(
            `Unexpected response from ${releasesUrl}. Status: ${response.status}`,
          );
        }
        return response.json();
      })
      .then((payload: LatestVersionData) => {
        let data: VersionData = payload;
        if (payload && payload.lts && showLTSOnly) {
          data = payload.lts;
        }
        // The data is not what we expect, so we can't show the notification.
        if (!data?.version) return;

        const latestVersion = new VersionNumber(data.version);
        const versionDelta = currentVersion.howMuchBehind(latestVersion);

        let releaseNotesUrl: string;
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

        if (this.hasLatestVersionTarget) {
          const versionLabel = [data.version, showLTSOnly ? '(LTS)' : '']
            .join(' ')
            .trim();
          this.latestVersionTarget.textContent = versionLabel;
        }

        if (this.hasLinkTarget) {
          this.linkTarget.setAttribute('href', releaseNotesUrl || '');
        }
        this.element.hidden = false;
      })
      .catch((err) => {
        // eslint-disable-next-line no-console
        console.error(`Error fetching ${releasesUrl}. Error: ${err}`);
      });
  }
}
