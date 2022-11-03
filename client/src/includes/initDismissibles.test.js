import { initDismissibles, updateDismissibles } from './initDismissibles';

jest.mock('../config/wagtailConfig.js', () => ({
  WAGTAIL_CONFIG: {
    ADMIN_URLS: { DISMISSIBLES: '/admin/dismissibles/' },
    CSRF_HEADER_NAME: 'X-CSRFToken',
    CSRF_TOKEN: 'test-token',
  },
}));

describe('initDismissibles', () => {
  it('should not error if there are no dismissibles', () => {
    document.body.innerHTML = '<div>CONTENT</div>';

    initDismissibles();

    expect(document.body.innerHTML).toContain('CONTENT');
  });

  describe('should initialise dismissibles', () => {
    it('for data-wagtail-dismissible-id and data-wagtail-dismissible-toggle attribute in parent and child', () => {
      document.body.innerHTML = `
      <article>
        <div data-wagtail-dismissible-id='test-id-1'>
          <div data-wagtail-dismissible-toggle></div>
        </div>
        <div data-wagtail-dismissible-id='test-id-2'>
          <div data-wagtail-dismissible-toggle></div>
        </div>
        <div data-wagtail-dismissible-id='test-id-3 data-wagtail-dismissible-toggle></div>
      </article>`;

      initDismissibles();

      // check the classes are initially empty
      expect(
        document.querySelector('[data-wagtail-dismissible-id]').classList,
      ).toHaveLength(0);

      // click all buttons
      document
        .querySelectorAll('[data-wagtail-dismissible-toggle]')
        .forEach((item) => {
          item.click();
        });

      // check the classes are updated and data attribute removed
      expect(
        [...document.querySelectorAll('[data-wagtail-dismissible-id]')].every(
          (item) =>
            item.classList.contains('w-dismissible--dismissed') &&
            item.getAttribute('data-wagtail-dismissed') === '',
        ),
      ).toBe(true);
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
        'X-CSRFToken': 'test-token',
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
