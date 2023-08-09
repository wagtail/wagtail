describe('Homepage', () => {
  beforeAll(async () => {
    await page.goto(`${TEST_ORIGIN}/admin/`, {
      waitUntil: 'domcontentloaded',
    });
  });

  it('has the right heading', async () => {
    const pageHeader = await page.$('h1');
    const pageHeaderValue = await pageHeader.evaluate((el) => el.textContent);
    expect(pageHeaderValue).toContain('Welcome to the Test Site Wagtail CMS');
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

  it('axe sidebar footer', async () => {
    const trigger = await page.$('[aria-label="Edit your account"]');
    await trigger.click();
    await expect(page).toPassAxeTests({
      include: '.sidebar-footer',
    });
  });
});
