jest.setTimeout(30000);

describe('Mobile sidebar toggle', () => {
  beforeEach(async () => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${TEST_ORIGIN}/admin/pages/add/demosite/standardpage/2/`);
  });

  it('stays aligned with the header as messages change height', async () => {
    const toggle = page
      .getByRole('button', {
        name: 'Toggle sidebar',
        exact: true,
      })
      .filter({ visible: true });
    const header = page.locator('.w-slim-header');

    const expectAligned = async () => {
      await page.waitForFunction(() => {
        const button = document.querySelector('.sidebar-nav-toggle');
        const slimHeader = document.querySelector('.w-slim-header');
        return (
          Math.abs(
            button.getBoundingClientRect().top -
              slimHeader.getBoundingClientRect().top,
          ) < 1
        );
      });
      expect(
        Math.abs(
          (await toggle.boundingBox()).y - (await header.boundingBox()).y,
        ),
      ).toBeLessThan(1);
    };

    await expectAligned();
    await page.evaluate(() => {
      document.dispatchEvent(
        new CustomEvent('w-messages:add', {
          detail: { type: 'success', text: 'The page has been saved.' },
        }),
      );
    });
    await page.waitForSelector('.messages .success');
    await expectAligned();

    await page.evaluate(() => {
      document.dispatchEvent(
        new CustomEvent('w-messages:add', {
          detail: {
            type: 'warning',
            text: 'This is a longer warning message that wraps onto multiple lines on a small screen.',
          },
        }),
      );
    });
    await page.waitForSelector('.messages .warning');
    await expectAligned();

    await toggle.click();
    expect((await toggle.boundingBox()).y).toBe(0);
    await toggle.click();
    await expectAligned();

    await page.setViewportSize({ width: 600, height: 844 });
    await expectAligned();

    await page.evaluate(() => {
      document.dispatchEvent(new CustomEvent('w-messages:clear'));
    });
    await page.waitForSelector('.messages li', { state: 'detached' });
    await expectAligned();
  });
});
