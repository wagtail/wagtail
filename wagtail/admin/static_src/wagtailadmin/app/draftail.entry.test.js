require('./draftail.entry');

describe('draftail.entry', () => {
  it('exposes global', () => {
    expect(window.draftail).toBeDefined();
  });

  it('has defaults registered', () => {
    expect(window.draftail.getPlugin('LINK')).toBeDefined();
    expect(window.draftail.getPlugin('DOCUMENT')).toBeDefined();
    expect(window.draftail.getPlugin('IMAGE')).toBeDefined();
    expect(window.draftail.getPlugin('EMBED')).toBeDefined();
  });
});
