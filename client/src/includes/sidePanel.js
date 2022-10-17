export default function initSidePanel() {
  const sidePanelWrapper = document.querySelector('[data-form-side]');

  // Abort if the side panel isn't available
  if (!sidePanelWrapper) return;

  // For now, we do not want to persist the side panel state in the explorer
  const inExplorer = 'formSideExplorer' in sidePanelWrapper.dataset;

  const setPanel = (panelName) => {
    const body = document.querySelector('body');
    const selectedPanel = document.querySelector(
      `[data-side-panel-toggle="${panelName}"]`,
    );

    // Abort if panelName is specified but it does not exist
    if (panelName && !selectedPanel) return;

    // Open / close side panel

    // HACK: For now, the comments will show without the side-panel opening.
    // They will later be updated so that they render inside the side panel.
    // We couldn't implement this for Wagtail 3.0 as the existing field styling
    // renders the "Add comment" button on the right hand side, and this gets
    // covered up by the side panel.

    if (panelName === '' || panelName === 'comments') {
      sidePanelWrapper.classList.remove('form-side--open');
      sidePanelWrapper.removeAttribute('aria-labelledby');
    } else {
      sidePanelWrapper.classList.add('form-side--open');
      sidePanelWrapper.setAttribute(
        'aria-labelledby',
        `side-panel-${panelName}-title`,
      );
    }

    document.querySelectorAll('[data-side-panel]').forEach((panel) => {
      if (panel.dataset.sidePanel === panelName) {
        if (panel.hidden) {
          // eslint-disable-next-line no-param-reassign
          panel.hidden = false;
          panel.dispatchEvent(new CustomEvent('show'));
          body.classList.add('side-panel-open');
        }
      } else if (!panel.hidden) {
        // eslint-disable-next-line no-param-reassign
        panel.hidden = true;
        panel.dispatchEvent(new CustomEvent('hide'));

        if (panelName === '') {
          body.classList.remove('side-panel-open');
        }
      }
    });

    // Update aria-expanded attribute on the panel toggles
    document.querySelectorAll('[data-side-panel-toggle]').forEach((toggle) => {
      toggle.setAttribute(
        'aria-expanded',
        toggle.dataset.sidePanelToggle === panelName ? 'true' : 'false',
      );
    });

    // Remember last opened side panel if not in explorer
    if (!inExplorer) {
      try {
        localStorage.setItem('wagtail:side-panel-open', panelName);
      } catch (e) {
        // Proceed without saving the last-open panel.
      }
    }
  };

  const togglePanel = (panelName) => {
    const isAlreadyOpen = !document
      .querySelector(`[data-side-panel="${panelName}"]`)
      .hasAttribute('hidden');

    if (isAlreadyOpen) {
      // Close the sidebar
      setPanel('');
    } else {
      // Open the sidebar / navigate to the panel
      setPanel(panelName);
    }
  };

  document.querySelectorAll('[data-side-panel-toggle]').forEach((toggle) => {
    toggle.addEventListener('click', () => {
      togglePanel(toggle.dataset.sidePanelToggle);
    });
  });

  const closeButton = document.querySelector('[data-form-side-close-button]');
  if (closeButton instanceof HTMLButtonElement) {
    closeButton.addEventListener('click', () => {
      setPanel('');
    });
  }

  // Open the last opened panel if not in explorer,
  // use timeout to allow comments to load first
  setTimeout(() => {
    try {
      const sidePanelOpen = localStorage.getItem('wagtail:side-panel-open');
      if (!inExplorer && sidePanelOpen) {
        setPanel(sidePanelOpen);
      }
    } catch (e) {
      // Proceed without remembering the last-open panel.
    }

    // Skip the animation on initial load only,
    // use timeout to ensure the panel has been triggered to open
    setTimeout(() => {
      sidePanelWrapper.classList.remove('form-side--initial');
    });
  });
}
