import Explorer, { ExplorerToggle, initExplorer } from './index';

describe('Explorer index', () => {
  it('exists', () => {
    expect(Explorer).toBeDefined();
  });

  describe('ExplorerToggle', () => {
    it('exists', () => {
      expect(ExplorerToggle).toBeDefined();
    });
  });

  describe('initExplorer', () => {
    it('exists', () => {
      expect(initExplorer).toBeInstanceOf(Function);
    });

    it('works', () => {
      document.body.innerHTML = '<div><div id="e"></div><div id="t">Test</div></div>';
      const explorerNode = document.querySelector('#e');
      const toggleNode = document.querySelector('#t');

      initExplorer(explorerNode, toggleNode);
      expect(document.body.innerHTML).toContain('data-reactroot');
    });
  });
});
