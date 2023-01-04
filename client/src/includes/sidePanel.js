import { ngettext } from '../utils/gettext';

export default function initSidePanel() {
  const sidePanelWrapper = document.querySelector('[data-form-side]');

  // Abort if the side panel isn't available
  if (!sidePanelWrapper) return;

  // For now, we do not want to persist the side panel state in the explorer
  const inExplorer = 'formSideExplorer' in sidePanelWrapper.dataset;

  const resizeGrip = document.querySelector('[data-form-side-resize-grip]');
  const widthInput = document.querySelector('[data-form-side-width-input]');

  const getSidePanelWidthStyles = () => {
    const sidePanelStyles = getComputedStyle(sidePanelWrapper);
    const minWidth = parseFloat(sidePanelStyles.minWidth);
    const maxWidth = parseFloat(sidePanelStyles.maxWidth);
    const width = parseFloat(sidePanelStyles.width);
    const range = maxWidth - minWidth;
    const percentage = ((width - minWidth) / range) * 100;

    return { minWidth, maxWidth, width, range, percentage };
  };

  let hidePanelTimeout;

  const setPanel = (panelName) => {
    clearTimeout(hidePanelTimeout);

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
      const name = panel.dataset.sidePanel;
      if (name === panelName) {
        if (panel.hidden) {
          // eslint-disable-next-line no-param-reassign
          panel.hidden = false;
          panel.dispatchEvent(new CustomEvent('show'));
          sidePanelWrapper.classList.add(`form-side--${name}`);
          body.classList.add('side-panel-open');
        }
      } else if (!panel.hidden) {
        const hidePanel = () => {
          // eslint-disable-next-line no-param-reassign
          panel.hidden = true;
          panel.dispatchEvent(new CustomEvent('hide'));
          sidePanelWrapper.classList.remove(`form-side--${name}`);
        };

        if (panelName === '') {
          body.classList.remove('side-panel-open');
          hidePanelTimeout = setTimeout(hidePanel, 500);
        } else {
          hidePanel();
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

      // Update width input percentage as each panel may have its own maxWidth
      // (e.g. the preview panel), use timeout to wait until the resize
      // transition has finished
      setTimeout(() => {
        const { percentage } = getSidePanelWidthStyles();
        // Invert the percentage to make the slider work in the opposite direction
        widthInput.value = 100 - percentage;
      }, 500);
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

  const setSidePanelWidth = (targetWidth) => {
    const { minWidth, maxWidth, range, width } = getSidePanelWidthStyles();
    const newWidth =
      parseInt(Math.max(minWidth, Math.min(targetWidth, maxWidth)), 10) ||
      width;

    const valueText = ngettext(
      '%(num)s pixel',
      '%(num)s pixels',
      newWidth,
    ).replace('%(num)s', newWidth);

    sidePanelWrapper.style.width = `${newWidth}px`;
    widthInput.value = 100 - ((newWidth - minWidth) / range) * 100;
    widthInput.setAttribute('aria-valuetext', valueText);

    // Save the new width to localStorage unless we're in the explorer
    if (inExplorer) return;
    try {
      localStorage.setItem('wagtail:side-panel-width', newWidth);
    } catch (e) {
      // Proceed without saving the side panel width.
    }
  };

  let startPos;
  let startWidth;

  const onPointerMove = (e) => {
    if (!e.screenX || !startPos || !startWidth) return;
    const delta = startPos - e.screenX;
    setSidePanelWidth(startWidth + delta);
  };

  resizeGrip.addEventListener('pointerdown', (e) => {
    // Remember the starting position and width of the side panel, so we can
    // calculate the new width based on the position change during the drag and
    // not resize the panel when it has gone past the minimum/maximum width.
    startPos = e.screenX;
    startWidth = getSidePanelWidthStyles().width;

    document.body.classList.add('side-panel-resizing');
    resizeGrip.setPointerCapture(e.pointerId);
    resizeGrip.addEventListener('pointermove', onPointerMove);
  });

  resizeGrip.addEventListener('pointerup', (e) => {
    resizeGrip.removeEventListener('pointermove', onPointerMove);
    resizeGrip.releasePointerCapture(e.pointerId);
    document.body.classList.remove('side-panel-resizing');
  });

  // Handle resizing with keyboard using a hidden range input.
  widthInput.addEventListener('change', (event) => {
    const { minWidth, range } = getSidePanelWidthStyles();
    const inputPercentage = 100 - parseInt(event.target.value, 10);
    const newWidth = minWidth + (range * inputPercentage) / 100;
    setSidePanelWidth(newWidth);
  });

  // Open the last opened panel if not in explorer,
  // use timeout to allow comments to load first
  setTimeout(() => {
    try {
      const sidePanelOpen = localStorage.getItem('wagtail:side-panel-open');
      if (!inExplorer && sidePanelOpen) {
        setPanel(sidePanelOpen);
      }
      setSidePanelWidth(localStorage.getItem('wagtail:side-panel-width'));
    } catch (e) {
      // Proceed without remembering the last-open panel and the panel width.
    }

    // Skip the animation on initial load only,
    // use timeout to ensure the panel has been triggered to open
    setTimeout(() => {
      sidePanelWrapper.classList.remove('form-side--initial');
    });
  });
}
