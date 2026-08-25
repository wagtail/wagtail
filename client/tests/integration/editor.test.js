jest.setTimeout(30000);

describe('Editor', () => {
  const globalEditorExcludes = '[aria-describedby^="placeholder-"]';
  beforeAll(async () => {
    await page.goto(`${TEST_ORIGIN}/admin/pages/add/demosite/standardpage/2/`);
  });

  it('has the right heading', async () => {
    const pageHeader = await page.$('h1');
    const pageHeaderValue = await pageHeader.evaluate((el) => el.textContent);
    expect(pageHeaderValue).toContain('New: Standard page');
  });

  it('axe', async () => {
    await expect(page).toPassAxeTests({
      exclude: `${globalEditorExcludes}`,
    });
  });

  it('axe InlinePanel', async () => {
    const trigger = await page.$('#id_carousel_items-ADD');
    trigger.click();
    await expect(page).toPassAxeTests({
      exclude: `${globalEditorExcludes}`,
    });
  });

  it.skip('axe embed chooser', async () => {
    const trigger = await page.$('.Draftail-Editor [name="EMBED"]');
    await Promise.all([
      trigger.click(),
      page.waitForSelector('.embed-form', { visible: true }),
    ]);
    await expect(page).toPassAxeTests({
      exclude: `${globalEditorExcludes}, .modal`,
    });
    await Promise.all([
      await page.keyboard.press('Escape'),
      page.waitForSelector('.Draftail-Editor--readonly', { hidden: true }),
    ]);
  });

  it.skip('axe image chooser', async () => {
    const trigger = await page.$('.Draftail-Editor [name="IMAGE"]');
    await Promise.all([
      trigger.click(),
      page.waitForSelector('.image-search', { visible: true }),
    ]);
    await expect(page).toPassAxeTests({
      exclude: `${globalEditorExcludes}, .modal`,
    });
    await Promise.all([
      await page.keyboard.press('Escape'),
      page.waitForSelector('.Draftail-Editor--readonly', { hidden: true }),
    ]);
  });

  it.skip('axe page chooser', async () => {
    const trigger = await page.$('.Draftail-Editor [name="LINK"]');
    await Promise.all([
      trigger.click(),
      page.waitForSelector('.page-results', { visible: true }),
    ]);
    await expect(page).toPassAxeTests({
      exclude: `${globalEditorExcludes}, .modal`,
    });
    await Promise.all([
      await page.keyboard.press('Escape'),
      page.waitForSelector('.Draftail-Editor--readonly', { hidden: true }),
    ]);
  });
});
