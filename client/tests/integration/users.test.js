describe('Users', () => {
  beforeAll(async () => {
    await page.goto('http://localhost:8000/admin/users/', { waitUntil: 'load' });
  });

  it('axe', async () => {
    const toggle = await page.$('[aria-label="Select all"]');
    await toggle.click();
    await expect(page).toPassAxeTests({
      exclude: '.skiplink, .sidebar__collapse-toggle, #wagtail-sidebar'
    });
  });
});
