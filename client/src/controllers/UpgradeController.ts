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
 * ```json
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
 * ```
 *
 * @example
 * ```html
 * <div
 *   data-controller="w-upgrade"
 *   data-w-upgrade-current-version-value="6.3.1"
 *   data-w-upgrade-url-value="https://path.to/latest.txt"
 * >
 *   <p>A new version of Wagtail is available!</p>
 * </div>
 * ```
 */
export class UpgradeController extends Controller<HTMLElement> {
  static targets = ['latestVersion', 'link', 'dismiss'];
  static values = {
    currentVersion: String,
    ltsOnly: { default: false, type: Boolean },
    url: { default: 'https://releases.wagtail.org/latest.txt', type: String },
  };

  declare readonly hasLatestVersionTarget: boolean;
  declare readonly hasLinkTarget: boolean;
  declare readonly hasDismissTarget: boolean;
  declare currentVersionValue: string;
  declare latestVersionTarget: HTMLElement;
  declare linkTarget: HTMLElement;
  declare dismissTarget: HTMLElement;
  declare ltsOnlyValue: any;
  declare urlValue: string;

  connect() {
    this.checkVersion();
  }

  /**
   * The version number that the user has acknowledged.
   *
   * Use the last dismissed version if it exists, or the current version otherwise.
   */
  get knownVersion() {
    return new VersionNumber(
      (this.hasDismissTarget &&
        this.dismissTarget.getAttribute('data-w-dismissible-value-param')) ||
        this.currentVersionValue,
    );
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

        // Do not show the notification if the current version is the latest
        // or the last dismissed (known) version is the latest.
        if (!versionDelta || !this.knownVersion.howMuchBehind(latestVersion)) {
          return;
        }

        // But use the actual installed version to check whether we want to
        // link to the feature release notes or the patch release notes.
        let releaseNotesUrl: string;
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

        if (this.hasDismissTarget) {
          this.dismissTarget.setAttribute(
            'data-w-dismissible-value-param',
            data.version,
          );
        }

        this.element.hidden = false;
      })
      .catch((err) => {
        // eslint-disable-next-line no-console
        console.error(`Error fetching ${releasesUrl}. Error: ${err}`);
      });
  }
}
