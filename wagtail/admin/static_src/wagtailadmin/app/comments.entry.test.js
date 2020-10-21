require('./comments.entry');

describe('comments.entry', () => {
  it('exposes module as global', () => {
    expect(window.comments).toBeDefined();
  });
});
