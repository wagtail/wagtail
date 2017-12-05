require('./draftail.entry');

describe('draftail.entry', () => {
  it('exposes global', () => {
    expect(window.draftail).toBeDefined();
  });
});
