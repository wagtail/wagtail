import {
  expandAllPanelsInTab,
  initCollapsiblePanel,
  toggleCollapsiblePanel,
} from './panels';

describe('expandAllPanelsInTab', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div id="tab-panel-1">
        <div data-panel>
          <button 
            id="panel-1-toggle" 
            data-panel-toggle 
            aria-controls="panel-1-content"
            aria-expanded="false"
          >
            Toggle Panel 1
          </button>
          <div id="panel-1-content" hidden>Content 1</div>
        </div>
        <div data-panel>
          <button 
            id="panel-2-toggle" 
            data-panel-toggle 
            aria-controls="panel-2-content"
            aria-expanded="true"
          >
            Toggle Panel 2
          </button>
          <div id="panel-2-content">Content 2</div>
        </div>
      </div>
      <div id="tab-panel-2">
        <div data-panel>
          <button 
            id="panel-3-toggle" 
            data-panel-toggle 
            aria-controls="panel-3-content"
            aria-expanded="false"
          >
            Toggle Panel 3
          </button>
          <div id="panel-3-content" hidden>Content 3</div>
        </div>
      </div>
    `;
  });

  it('should expand all collapsed panels in the specified tab', () => {
    // Initially, panel-1 is collapsed (aria-expanded="false")
    const panel1Toggle = document.getElementById('panel-1-toggle');
    expect(panel1Toggle.getAttribute('aria-expanded')).toBe('false');

    // Expand all panels in tab-panel-1
    expandAllPanelsInTab('tab-panel-1');

    // Panel 1 should now be expanded
    expect(panel1Toggle.getAttribute('aria-expanded')).toBe('true');
    const panel1Content = document.getElementById('panel-1-content');
    expect(panel1Content.hasAttribute('hidden')).toBe(false);

    // Panel 2 was already expanded, should remain expanded
    const panel2Toggle = document.getElementById('panel-2-toggle');
    expect(panel2Toggle.getAttribute('aria-expanded')).toBe('true');
  });

  it('should not affect panels in other tabs', () => {
    // Panel 3 in tab-panel-2 is collapsed
    const panel3Toggle = document.getElementById('panel-3-toggle');
    expect(panel3Toggle.getAttribute('aria-expanded')).toBe('false');

    // Expand all panels in tab-panel-1 (not tab-panel-2)
    expandAllPanelsInTab('tab-panel-1');

    // Panel 3 should remain collapsed
    expect(panel3Toggle.getAttribute('aria-expanded')).toBe('false');
    const panel3Content = document.getElementById('panel-3-content');
    expect(panel3Content.hasAttribute('hidden')).toBe(true);
  });

  it('should handle non-existent tab panel gracefully', () => {
    // Should not throw an error
    expect(() => expandAllPanelsInTab('non-existent-panel')).not.toThrow();
  });

  it('should handle empty tab panel', () => {
    document.body.innerHTML = '<div id="empty-tab"></div>';
    expect(() => expandAllPanelsInTab('empty-tab')).not.toThrow();
  });
});

describe('toggleCollapsiblePanel', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <div data-panel>
        <button 
          id="test-toggle" 
          data-panel-toggle 
          aria-controls="test-content"
          aria-expanded="true"
        >
          Toggle
        </button>
        <div id="test-content">Content</div>
      </div>
    `;
  });

  it('should collapse a panel when isExpanding is false', () => {
    const toggle = document.getElementById('test-toggle');
    toggleCollapsiblePanel(toggle, false);

    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    const content = document.getElementById('test-content');
    expect(content.hasAttribute('hidden')).toBe(true);
  });

  it('should expand a panel when isExpanding is true', () => {
    const toggle = document.getElementById('test-toggle');
    // First collapse it
    toggleCollapsiblePanel(toggle, false);
    expect(toggle.getAttribute('aria-expanded')).toBe('false');

    // Then expand it
    toggleCollapsiblePanel(toggle, true);
    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    const content = document.getElementById('test-content');
    expect(content.hasAttribute('hidden')).toBe(false);
  });
});
