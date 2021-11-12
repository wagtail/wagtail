describe('Listing', () => {
  beforeAll(async () => {
    await page.goto('http://localhost:8000/admin/pages/2/');
  });

  it('has the right heading', async () => {
    expect(await page.title()).toContain('Wagtail - Exploring Welcome to your new Wagtail site!');
  });

  it('axe', async () => {
    await expect(page).toPassAxeTests({
      exclude: '.skiplink, .sidebar__collapse-toggle, #wagtail-sidebar, a[href$="dummy-button"]'
    });
  });
});
