describe('Groups', () => {
  beforeAll(async () => {
    await page.goto(`${TEST_ORIGIN}/admin/groups/2/`);
  }, 10000);

  it('has the right heading', async () => {
    expect(await page.title()).toContain('Wagtail - Editing Editors');
  });

  it('axe', async () => {
    await expect(page).toPassAxeTests({
      exclude: '.skiplink, .sidebar__collapse-toggle, #wagtail-sidebar',
    });
  });
});
