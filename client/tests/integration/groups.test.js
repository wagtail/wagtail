jest.setTimeout(30000);

describe('Groups', () => {
  beforeAll(async () => {
    await page.goto(`${TEST_ORIGIN}/admin/groups/edit/2/`);
  });

  it('has the right heading', async () => {
    expect(await page.title()).toContain('Editing: Editors - Wagtail');
  });

  it('axe', async () => {
    await expect(page).toPassAxeTests({
      exclude: '.skiplink, .sidebar__collapse-toggle, #wagtail-sidebar',
    });
  });
});
