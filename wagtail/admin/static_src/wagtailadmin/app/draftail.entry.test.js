require('./draftail.entry');

describe('draftail.entry', () => {
  it('exposes global', () => {
    expect(window.draftail).toBeDefined();
  });

  it('has defaults registered', () => {
    expect(window.draftail.getSource('ModalWorkflowSource')).toBeDefined();
    expect(window.draftail.getDecorator('Link')).toBeDefined();
    expect(window.draftail.getDecorator('Document')).toBeDefined();
    expect(window.draftail.getBlock('ImageBlock')).toBeDefined();
    expect(window.draftail.getBlock('EmbedBlock')).toBeDefined();
  });
});
