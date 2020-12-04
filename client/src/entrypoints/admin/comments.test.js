require('./comments');

describe('comments', () => {
  it('exposes module as global', () => {
    expect(window.comments).toBeDefined();
  });
});
