const path = require('node:path');

const CLIENT_FIXTURES = path.join(__dirname, '..', 'fixtures');
const IMAGES_FIXTURES = path.join(
  __dirname,
  '..',
  '..',
  '..',
  'wagtail',
  'images',
  'tests',
  'image_files',
);

jest.setTimeout(30000);

describe('Images Upload', () => {
  it('can upload and delete an image', async () => {
    page.setDefaultTimeout(5_000);
    await page.goto(`${TEST_ORIGIN}/admin/images/`);
    await page.getByRole('link', { name: /add an image/i }).click();
    const input = page.locator('css=input[type="file"]');
    await input.waitFor();
    await expect(await input.count()).toBeGreaterThanOrEqual(1);

    await input.setInputFiles(path.join(IMAGES_FIXTURES, 'landscape_1.jpg'));

    // Expect that we see the edit form.
    await page.getByLabel('Title*').waitFor();
    await page.getByLabel('Description').waitFor();

    // Check that the image is created and listed in the images view.
    await page.goto(`${TEST_ORIGIN}/admin/images/`);
    await page.getByText('landscape_1').waitFor();

    // And delete it.
    await page.getByRole('checkbox', { description: 'landscape_1' }).check();
    await page.getByText('1 image selected').waitFor();
    await page.getByRole('link', { name: /delete/i }).click();
    await page.getByRole('button', { name: /yes, delete/i }).click();
    await page.getByText('1 image has been deleted').waitFor();
    expect(await page.getByText('landscape_1').count()).toEqual(0);
  });

  it('cannot upload an image that is too big', async () => {
    await page.goto(`${TEST_ORIGIN}/admin/images/`);
    await page.getByRole('link', { name: /add an image/i }).click();
    const input = page.locator('css=input[type="file"]');
    await input.waitFor();

    // We want to make sure client-side validation prevents any uploading.
    let didPost = false;
    page.on('request', (request) => {
      didPost ||=
        request.method() === 'POST' &&
        request.url().includes('/admin/images/multiple/add/');
    });

    await input.setInputFiles(path.join(CLIENT_FIXTURES, 'image-big.png'));
    await page.getByText('This file is too big').waitFor();
    expect(didPost).toBeFalsy();
  });
});
