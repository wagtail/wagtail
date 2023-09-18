import { Application } from '@hotwired/stimulus';

import { UpgradeController } from './UpgradeController';

describe('UpgradeController', () => {
  let application;
  const url = 'https://releases.wagtail.org/mock.txt';
  const version = '2.3';

  beforeEach(() => {
    document.body.innerHTML = `
    <div
      class="panel w-hidden"
      id="panel"
      data-controller="w-upgrade"
      data-w-upgrade-current-version-value="${version}"
      data-w-upgrade-hidden-class="w-hidden"
      data-w-upgrade-url-value="${url}"
    >
      <div class="help-block help-warning">
        Your version: <strong>${version}</strong>.
        New version: <strong id="latest-version" data-w-upgrade-target="latestVersion">_</strong>.
        <a href="" id="link" data-w-upgrade-target="link">Release notes</a>
      </div>
    </div>`;
  });

  afterEach(() => {
    jest.clearAllMocks();
    application.stop();
  });

  it('should keep the hidden class by default & then show a message when version is out of date', async () => {
    const data = {
      version: '5.15.1',
      url: 'https://docs.wagtail.org/latest/url',
      minorUrl: 'https://docs.wagtail.org/latest-minor/url',
      lts: {
        version: '5.12.2',
        url: 'https://docs.wagtail.org/lts/url',
        minorUrl: 'https://docs.wagtail.org/lts-minor/url',
      },
    };

    expect(global.fetch).not.toHaveBeenCalled();

    fetch.mockResponseSuccess(JSON.stringify(data));

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // trigger next browser render cycle
    await Promise.resolve();

    expect(global.fetch).toHaveBeenCalledWith(
      'https://releases.wagtail.org/mock.txt',
      { referrerPolicy: 'strict-origin-when-cross-origin' },
    );

    expect(
      document.getElementById('panel').classList.contains('w-hidden'),
    ).toBe(true);

    await new Promise(requestAnimationFrame);

    // should remove the hidden class on success
    expect(
      document.getElementById('panel').classList.contains('w-hidden'),
    ).toBe(false);

    // should update the latest version number in the text
    expect(document.getElementById('latest-version').textContent).toBe(
      data.version,
    );

    // should add the latest version link
    expect(document.getElementById('link').getAttribute('href')).toEqual(
      data.minorUrl,
    );
  });

  it('should not show the message if the current version is up to date', async () => {
    const data = {
      version: '5.15.1',
      url: 'https://docs.wagtail.org/latest/url',
      minorUrl: 'https://docs.wagtail.org/latest-minor/url',
      lts: {
        version: '2.2',
        url: 'https://docs.wagtail.org/lts/url',
        minorUrl: 'https://docs.wagtail.org/lts-minor/url',
      },
    };

    fetch.mockResponseSuccess(JSON.stringify(data));

    expect(global.fetch).not.toHaveBeenCalled();

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // trigger next browser render cycle
    await Promise.resolve();

    expect(
      document.getElementById('panel').classList.contains('w-hidden'),
    ).toBe(true);
  });

  it('should throw an error if the fetch fails', async () => {
    // Spy on console.error to verify that it is called with the expected error message
    jest.spyOn(console, 'error').mockImplementation(() => {});

    // Create a mock for the fetch function that returns a rejected Promise
    const mockFetch = jest.fn(() => Promise.reject(new Error('Fetch failed')));

    // Replace the global fetch function with the mock
    global.fetch = mockFetch;

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // Wait for the catch block to be executed
    await new Promise(requestAnimationFrame);

    // Verify that console.error was called with the expected error message
    /* eslint-disable-next-line no-console */
    expect(console.error).toHaveBeenCalledWith(
      `Error fetching ${url}. Error: Error: Fetch failed`,
    );

    // Restore the original implementation of console.error
    /* eslint-disable no-console */
    console.error.mockRestore();
  });
});
