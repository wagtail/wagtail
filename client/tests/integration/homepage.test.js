jest.setTimeout(30000);

describe('Homepage', () => {
  beforeAll(async () => {
    await page.goto(`${TEST_ORIGIN}/admin/`, {
      waitUntil: 'domcontentloaded',
    });
  });

  it('has the right heading', async () => {
    const pageHeader = await page.$('h1');
    const pageHeaderValue = await pageHeader.evaluate((el) => el.textContent);
    expect(pageHeaderValue).toContain('Test Site');
  });

  it('axe', async () => {
    await expect(page).toPassAxeTests({
      exclude: '.stats, .skiplink, #wagtail-sidebar, .sidebar__collapse-toggle',
    });
  });

  it('axe page explorer', async () => {
    const trigger = await page.$(
      '.sidebar-page-explorer-item [aria-haspopup="dialog"]',
    );
    await trigger.click();
    await expect(page).toPassAxeTests({
      include: '.sidebar-main-menu',
    });
  });

  it('axe sidebar sub-menu', async () => {
    const trigger = await page.$(
      '.sidebar-sub-menu-item [aria-haspopup="menu"]',
    );
    await trigger.click();
    await expect(page).toPassAxeTests({
      include: '.sidebar-main-menu',
    });
  });
});
