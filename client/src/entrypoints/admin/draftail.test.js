require('./draftail');

describe('draftail', () => {
  it('exposes module as global', () => {
    expect(window.draftail).toBeDefined();
  });

  it('exposes package as global', () => {
    expect(window.Draftail).toBeDefined();
  });

  it('has defaults registered', () => {
    expect(Object.keys(window.draftail.registerPlugin({}))).toEqual([
      'DOCUMENT',
      'LINK',
      'IMAGE',
      'EMBED',
      'undefined',
    ]);
  });
});
