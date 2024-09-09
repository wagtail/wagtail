jest.setTimeout(30000);

describe('Listing', () => {
  beforeAll(async () => {
    await page.goto(`${TEST_ORIGIN}/admin/pages/2/`);
  });

  it('has the right heading', async () => {
    expect(await page.title()).toContain(
      'Exploring: Welcome to your new Wagtail site! - Wagtail',
    );
  });

  it('axe', async () => {
    await expect(page).toPassAxeTests({
      exclude:
        '.skiplink, .sidebar__collapse-toggle, #wagtail-sidebar, a[href$="dummy-button"]',
    });
  });
});
