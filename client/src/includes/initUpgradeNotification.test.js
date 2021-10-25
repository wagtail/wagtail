import { initUpgradeNotification } from './initUpgradeNotification';

// https://stackoverflow.com/a/51045733
const flushPromises = () => new Promise(setImmediate);

describe('initUpgradeNotification', () => {
  const version = '2.3';

  document.body.innerHTML = `
  <div
    class="panel"
    id="panel"
    data-upgrade-notification
    data-current-version="${version}"
    style="display:none"
  >
      <div class="help-block help-warning">
          Your version: <strong>${version}</strong>.
          New version: <strong id="latest-version" data-upgrade-version></strong>.
          <a href="" id="link" data-upgrade-link>Release notes</a>
      </div>
  </div>
  `;

  it('should show the notification and update the version & link', async () => {
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

    fetch.mockResponseSuccess(JSON.stringify(data));

    expect(global.fetch).not.toHaveBeenCalled();

    initUpgradeNotification();

    // trigger next browser render cycle
    await Promise.resolve(true);

    expect(global.fetch).toHaveBeenCalledWith(
      'https://releases.wagtail.io/latest.txt',
      { referrerPolicy: 'strict-origin-when-cross-origin' },
    );
    expect(document.getElementById('panel').style.display).toBe('none');

    await flushPromises();

    // should remove the hidden class on success
    expect(document.getElementById('panel').style.display).toBe('');

    // should update the version in the message
    expect(document.getElementById('latest-version').innerText).toEqual(
      data.version,
    );

    // should update the link
    expect(document.getElementById('link').getAttribute('href')).toEqual(
      data.minorUrl,
    );
  });
});
