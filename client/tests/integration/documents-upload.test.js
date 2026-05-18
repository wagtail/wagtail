const fs = require('node:fs/promises');
const path = require('node:path');
const { after } = require('node:test');

jest.setTimeout(30000);

describe('Documents Upload', () => {
  let tempFolder;
  let smallFile;
  let bigFile;

  beforeAll(async () => {
    tempFolder = await fs.mkdtemp('wagtail-documents-test');
    smallFile = path.join(tempFolder, 'small-file.txt');
    await fs.writeFile(smallFile, 'Hello', { encoding: 'utf-8' });
    bigFile = path.join(tempFolder, 'big-file.txt');
    await fs.writeFile(bigFile, Buffer.alloc(600 * 1024, 'Hello '), {
      encoding: 'utf-8',
    });
  });

  afterAll(async () => {
    if (tempFolder) {
      await fs.rm(tempFolder, { force: true, recursive: true });
    }
  });

  it('can upload and delete a document', async () => {
    page.setDefaultTimeout(5_000);
    await page.goto(`${TEST_ORIGIN}/admin/documents/`);
    await page.getByRole('link', { name: /add a document/i }).click();
    const input = page.locator('css=input[type="file"]');
    await input.waitFor();
    await expect(await input.count()).toBeGreaterThanOrEqual(1);

    await input.setInputFiles(smallFile);

    // Expect that we see the edit form.
    await page.getByLabel('Title*').waitFor();

    // Check that the document is created and shown in the listing view.
    await page.goto(`${TEST_ORIGIN}/admin/documents/`);
    const checkbox = page
      .locator('tr')
      .filter({ hasText: 'small-file' })
      .getByRole('checkbox');
    await checkbox.waitFor();

    // And delete it.
    await checkbox.check();
    await page.getByText('1 document selected').waitFor();
    await page.getByRole('link', { name: /delete/i }).click();
    await page.getByRole('button', { name: /yes, delete/i }).click();
    await page.getByText('1 document has been deleted').waitFor();
    expect(await page.getByText('small-file').count()).toEqual(0);
  });

  it('cannot upload a document that is too big', async () => {
    await page.goto(`${TEST_ORIGIN}/admin/documents/`);
    await page.getByRole('link', { name: /add a document/i }).click();
    const input = page.locator('css=input[type="file"]');
    await input.waitFor();

    // We want to make sure client-side validation prevents any uploading.
    let didPost = false;
    page.on('request', (request) => {
      didPost ||=
        request.method() === 'POST' &&
        request.url().includes('/admin/documents/multiple/add/');
    });

    await input.setInputFiles(bigFile);
    await page.getByText('This file is too big').waitFor();
    expect(didPost).toBeFalsy();
  });
});
