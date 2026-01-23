import { Application } from '@hotwired/stimulus';
import {
  DismissibleController,
  updateDismissibles,
} from './DismissibleController';

jest.mock('../config/wagtailConfig.ts', () => ({
  WAGTAIL_CONFIG: {
    ...jest.requireActual('../config/wagtailConfig.ts').WAGTAIL_CONFIG,
    ADMIN_URLS: { DISMISSIBLES: '/admin/dismissibles/' },
  },
}));

describe('DismissibleController', () => {
  let application;
  const data = { whats_new_in_wagtail_version_4: true };

  beforeEach(() => {
    application?.stop();

    document.body.innerHTML = `
    <section
      id="main-content"
      data-controller="w-dismissible"
      data-w-dismissible-dismissed-class="w-dismissible--dismissed"
      data-w-dismissible-id-value="whats_new_in_wagtail_version_4"
      data-w-dismissible-target="content"
    >
      <button type="button" data-action="w-dismissible#toggle">X</button>
    </section>`;

    application = Application.start();
    application.register('w-dismissible', DismissibleController);
  });

  afterEach(() => {
    global.fetch.mockClear();
  });

  it("should add a 'dismissed' class and attribute when the dismiss button is clicked", () => {
    const button = document.querySelector('button');
    const mainContent = document.querySelector('#main-content');

    expect(mainContent.classList).toHaveLength(0);
    expect(
      mainContent.getAttribute('data-w-dismissible-dismissed-value'),
    ).toBeFalsy();
    expect(mainContent.classList).not.toContain('w-dismissible--dismissed');

    button.click();

    expect(mainContent.classList).toContain('w-dismissible--dismissed');
    expect(mainContent.getAttribute('data-w-dismissible-dismissed-value')).toBe(
      'true',
    );
  });

  it('should update the dismissible ids when the dismiss button is clicked', async () => {
    expect.assertions(1);

    const button = document.querySelector('button');

    button.click();

    await expect(global.fetch).toHaveBeenCalledWith('/admin/dismissibles/', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'x-xsrf-token': 'potato',
      },
      body: JSON.stringify(data),
      mode: 'same-origin',
    });
  });

  it('should toggle the client-side state without calling the server if the ID is missing', async () => {
    const button = document.querySelector('button');
    const mainContent = document.querySelector('#main-content');
    mainContent.removeAttribute('data-w-dismissible-id-value');
    await Promise.resolve();

    expect(mainContent.classList).toHaveLength(0);
    expect(
      mainContent.getAttribute('data-w-dismissible-dismissed-value'),
    ).toBeFalsy();
    expect(mainContent.classList).not.toContain('w-dismissible--dismissed');
    expect(global.fetch).not.toHaveBeenCalled();

    button.click();

    expect(mainContent.classList).toContain('w-dismissible--dismissed');
    expect(mainContent.getAttribute('data-w-dismissible-dismissed-value')).toBe(
      'true',
    );
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('should allow customizing the update value via params', async () => {
    expect.assertions(1);

    const mainContent = document.querySelector('#main-content');
    mainContent.setAttribute(
      'data-w-dismissible-id-value',
      'last_upgrade_check',
    );
    const button = document.querySelector('button');
    button.setAttribute('data-w-dismissible-value-param', '6.3.1');
    await Promise.resolve();

    button.click();

    await expect(global.fetch).toHaveBeenCalledWith('/admin/dismissibles/', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'x-xsrf-token': 'potato',
      },
      body: JSON.stringify({ last_upgrade_check: '6.3.1' }),
      mode: 'same-origin',
    });
  });
});

describe('updateDismissibles', () => {
  const data = { 'test-id-1': true };
  document.body.innerHTML = `<div data-wagtail-dismissible-id='test-id-1' data-wagtail-dismissible-toggle></div>`;

  it('should update the dismissible ids', async () => {
    expect.assertions(1);

    updateDismissibles(data);

    await expect(global.fetch).toHaveBeenCalledWith('/admin/dismissibles/', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'x-xsrf-token': 'potato',
      },
      body: JSON.stringify(data),
      mode: 'same-origin',
    });
  });

  it('should not update the dismissible ids', async () => {
    expect.assertions(1);

    updateDismissibles(data);

    global.fetch.mockRejectedValueOnce(new Error('error'));
    await expect(updateDismissibles(data)).rejects.toThrowError('error');
  });
});
