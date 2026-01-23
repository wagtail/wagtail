import { Application } from '@hotwired/stimulus';

import { UpgradeController } from './UpgradeController';

describe('UpgradeController', () => {
  let application;
  const url = 'https://releases.wagtail.org/mock.txt';
  const version = '2.3';

  beforeEach(() => {
    document.body.innerHTML = /* html */ `
    <div
      class="panel"
      id="panel"
      data-controller="w-upgrade"
      data-w-upgrade-current-version-value="${version}"
      data-w-upgrade-url-value="${url}"
      hidden
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

  it('should keep the hidden attribute by default & then show a message when version is out of date', async () => {
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

    fetch.mockResponseSuccessJSON(JSON.stringify(data));

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // trigger next browser render cycle
    await Promise.resolve();

    expect(global.fetch).toHaveBeenCalledWith(
      'https://releases.wagtail.org/mock.txt',
      { referrerPolicy: 'strict-origin-when-cross-origin' },
    );

    expect(document.getElementById('panel').hidden).toBe(true);

    await new Promise(requestAnimationFrame);

    // should remove the hidden class on success
    expect(document.getElementById('panel').hidden).toBe(false);

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
      version: '2.3',
      url: 'https://docs.wagtail.org/latest/url',
      minorUrl: 'https://docs.wagtail.org/latest-minor/url',
      lts: {
        version: '2.2',
        url: 'https://docs.wagtail.org/lts/url',
        minorUrl: 'https://docs.wagtail.org/lts-minor/url',
      },
    };

    fetch.mockResponseSuccessJSON(JSON.stringify(data));

    expect(global.fetch).not.toHaveBeenCalled();

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // trigger next browser render cycle
    await Promise.resolve();

    expect(global.fetch).toHaveBeenCalledWith(
      'https://releases.wagtail.org/mock.txt',
      { referrerPolicy: 'strict-origin-when-cross-origin' },
    );

    expect(document.getElementById('panel').hidden).toBe(true);

    await new Promise(requestAnimationFrame);

    // should keep the hidden attribute
    expect(document.getElementById('panel').hidden).toBe(true);
  });

  it('should not show the message if the version has been dismissed before', async () => {
    const data = {
      version: '6.2.2',
      url: 'https://docs.wagtail.org/latest/url',
      minorUrl: 'https://docs.wagtail.org/latest-minor/url',
      lts: {
        version: '5.2.6',
        url: 'https://docs.wagtail.org/lts/url',
        minorUrl: 'https://docs.wagtail.org/lts-minor/url',
      },
    };

    fetch.mockResponseSuccessJSON(JSON.stringify(data));

    expect(global.fetch).not.toHaveBeenCalled();
    const panel = document.getElementById('panel');
    const dismissButton = document.createElement('button');
    dismissButton.setAttribute('data-w-upgrade-target', 'dismiss');
    panel.appendChild(dismissButton);

    // Last dismissed version is 6.2.2 (the same as the latest version)
    dismissButton.setAttribute('data-w-dismissible-value-param', '6.2.2');

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // trigger next browser render cycle
    await Promise.resolve();

    expect(global.fetch).toHaveBeenCalledWith(
      'https://releases.wagtail.org/mock.txt',
      { referrerPolicy: 'strict-origin-when-cross-origin' },
    );

    expect(document.getElementById('panel').hidden).toBe(true);

    await new Promise(requestAnimationFrame);

    // should remove the hidden class on success
    expect(document.getElementById('panel').hidden).toBe(true);
  });

  it('should show the message if the last dismissed version is not the latest', async () => {
    const data = {
      version: '6.2.3',
      url: 'https://docs.wagtail.org/latest/url',
      minorUrl: 'https://docs.wagtail.org/latest-minor/url',
      lts: {
        version: '5.2.9', // latest LTS version
        url: 'https://docs.wagtail.org/lts/url',
        minorUrl: 'https://docs.wagtail.org/lts-minor/url',
      },
    };

    fetch.mockResponseSuccessJSON(JSON.stringify(data));

    expect(global.fetch).not.toHaveBeenCalled();
    const panel = document.getElementById('panel');
    const dismissButton = document.createElement('button');
    dismissButton.setAttribute('data-w-upgrade-target', 'dismiss');
    panel.appendChild(dismissButton);

    // Simulate the case where we only care about LTS versions
    panel.setAttribute('data-w-upgrade-lts-only-value', 'true');
    // Last dismissed version is 5.2.6
    dismissButton.setAttribute('data-w-dismissible-value-param', '5.2.6');
    // Current installed version is 4.1.2
    panel.setAttribute('data-w-upgrade-current-version-value', '4.1.2');

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // trigger next browser render cycle
    await Promise.resolve();

    expect(global.fetch).toHaveBeenCalledWith(
      'https://releases.wagtail.org/mock.txt',
      { referrerPolicy: 'strict-origin-when-cross-origin' },
    );

    expect(document.getElementById('panel').hidden).toBe(true);

    await new Promise(requestAnimationFrame);

    // should remove the hidden class on success
    expect(document.getElementById('panel').hidden).toBe(false);

    // should update the latest version number in the text
    // and include the (LTS) label since we only care about the LTS versions
    expect(document.getElementById('latest-version').textContent).toBe(
      `${data.lts.version} (LTS)`,
    );

    // should add the link using the minorUrl,
    // since the actual installed version is way behind, i.e. 4.1.2 vs 5.2.9,
    // even though the last dismissed version is 5.2.6
    expect(document.getElementById('link').getAttribute('href')).toEqual(
      data.lts.minorUrl,
    );

    // Should update the dismissible value param to the latest LTS version,
    // so this version is not shown again if the user dismisses it
    expect(
      document
        .querySelector('[data-w-upgrade-target="dismiss"]')
        .getAttribute('data-w-dismissible-value-param'),
    ).toEqual('5.2.9');
  });

  it('should not show the message if the last dismissed version is not the latest but the current version is', async () => {
    const data = {
      version: '6.4.2',
      url: 'https://docs.wagtail.org/latest/url',
      minorUrl: 'https://docs.wagtail.org/latest-minor/url',
      lts: {
        version: '6.3.4',
        url: 'https://docs.wagtail.org/lts/url',
        minorUrl: 'https://docs.wagtail.org/lts-minor/url',
      },
    };

    fetch.mockResponseSuccessJSON(JSON.stringify(data));

    expect(global.fetch).not.toHaveBeenCalled();
    const panel = document.getElementById('panel');
    const dismissButton = document.createElement('button');
    dismissButton.setAttribute('data-w-upgrade-target', 'dismiss');
    panel.appendChild(dismissButton);

    // Last dismissed version is 6.4.1
    dismissButton.setAttribute('data-w-dismissible-value-param', '6.4.1');
    // Current installed version is 6.4.2
    panel.setAttribute('data-w-upgrade-current-version-value', '6.4.2');

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // trigger next browser render cycle
    await Promise.resolve();

    expect(global.fetch).toHaveBeenCalledWith(
      'https://releases.wagtail.org/mock.txt',
      { referrerPolicy: 'strict-origin-when-cross-origin' },
    );

    expect(document.getElementById('panel').hidden).toBe(true);

    await new Promise(requestAnimationFrame);

    // should keep the hidden class on success,
    // because the installed version is already the latest
    expect(document.getElementById('panel').hidden).toBe(true);
  });

  it('should use the latest URL if the currently installed version is at the same minor version', async () => {
    const data = {
      version: '6.2.6',
      url: 'https://docs.wagtail.org/latest/url',
      minorUrl: 'https://docs.wagtail.org/latest-minor/url',
      lts: {
        version: '5.2.6',
        url: 'https://docs.wagtail.org/lts/url',
        minorUrl: 'https://docs.wagtail.org/lts-minor/url',
      },
    };

    fetch.mockResponseSuccessJSON(JSON.stringify(data));

    expect(global.fetch).not.toHaveBeenCalled();
    const panel = document.getElementById('panel');
    const dismissButton = document.createElement('button');
    dismissButton.setAttribute('data-w-upgrade-target', 'dismiss');
    panel.appendChild(dismissButton);

    // Last dismissed version is 6.2.2
    dismissButton.setAttribute('data-w-dismissible-value-param', '6.2.2');
    // Current installed version is 6.2.3
    panel.setAttribute('data-w-upgrade-current-version-value', '6.2.3');

    // start application
    application = Application.start();
    application.register('w-upgrade', UpgradeController);

    // trigger next browser render cycle
    await Promise.resolve();

    expect(global.fetch).toHaveBeenCalledWith(
      'https://releases.wagtail.org/mock.txt',
      { referrerPolicy: 'strict-origin-when-cross-origin' },
    );

    expect(document.getElementById('panel').hidden).toBe(true);

    await new Promise(requestAnimationFrame);

    // should remove the hidden class on success
    expect(document.getElementById('panel').hidden).toBe(false);

    // should update the latest version number in the text
    expect(document.getElementById('latest-version').textContent).toBe(
      data.version,
    );

    // should add the latest version link using the latest version,
    // since the actual installed version is not far behind (6.2.3 vs 6.2.6)
    expect(document.getElementById('link').getAttribute('href')).toEqual(
      data.url,
    );

    // Should update the dismissible value param to the latest version,
    // so this version is not shown again if the user dismisses it
    expect(
      document
        .querySelector('[data-w-upgrade-target="dismiss"]')
        .getAttribute('data-w-dismissible-value-param'),
    ).toEqual('6.2.6');
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
