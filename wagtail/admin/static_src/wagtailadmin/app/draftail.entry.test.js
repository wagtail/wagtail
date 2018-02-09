require('./draftail.entry');

describe('draftail.entry', () => {
  it('exposes global', () => {
    expect(window.draftail).toBeDefined();
  });

  it('has defaults registered', () => {
    expect(Object.keys(window.draftail.registerPlugin({}))).toEqual(["DOCUMENT", "LINK", "IMAGE", "EMBED", "undefined"]);
  });
});
