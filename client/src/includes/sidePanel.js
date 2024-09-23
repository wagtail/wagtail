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

  // We force the slider input to have dir="ltr" in the HTML so that the slider
  // works the same way across Safari, Chrome and Firefox. Here, we correct the
  // percentage value to follow the direction set on the root <html> element.
  const getDirectedPercentage = (value) =>
    document.documentElement.dir === 'rtl' ? value : 100 - value;

  let hidePanelTimeout;

  const setPanel = (panelName) => {
    clearTimeout(hidePanelTimeout);

    const body = document.querySelector('body');
    const selectedPanel = document.querySelector(
      `[data-side-panel="${panelName}"]`,
    );

    // Abort if panelName is specified but it does not exist
    if (panelName && !selectedPanel) return;

    // Open / close side panel
    if (panelName === '') {
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
          // Don't fire the show event just yet,
          // to ensure that the hide event for the other panels is fired first.
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

    if (selectedPanel) {
      // Dispatch the show event after all the toggling logic is done
      selectedPanel.dispatchEvent(new CustomEvent('show'));
    }

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
        widthInput.value = getDirectedPercentage(percentage);
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

  // Open the side panel if the 'open' custom event is triggered on the side panel
  // This is allows panels to be opened with JavaScript without hacking the toggle
  document.querySelectorAll('[data-side-panel]').forEach((panel) => {
    panel.addEventListener('open', () => {
      setPanel(panel.dataset.sidePanel);
    });
  });

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

    document.documentElement.style.setProperty(
      '--side-panel-width',
      `${newWidth}px`,
    );
    const inputPercentage = ((newWidth - minWidth) / range) * 100;
    widthInput.value = getDirectedPercentage(inputPercentage);
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
    const direction = document.documentElement.dir === 'rtl' ? -1 : 1;
    const delta = startPos - e.screenX;
    setSidePanelWidth(startWidth + delta * direction);
  };

  const onPointerUp = (e) => {
    resizeGrip.releasePointerCapture(e.pointerId);
    resizeGrip.removeEventListener('pointermove', onPointerMove);
    document.removeEventListener('pointerup', onPointerUp);
    document.body.classList.remove('side-panel-resizing');
  };

  resizeGrip.addEventListener('pointerdown', (e) => {
    // Ignore right-click, because it opens the context menu and doesn't trigger
    // pointerup when the click is released.
    if (e.button !== 0) return;

    // Remember the starting position and width of the side panel, so we can
    // calculate the new width based on the position change during the drag and
    // not resize the panel when it has gone past the minimum/maximum width.
    startPos = e.screenX;
    startWidth = getSidePanelWidthStyles().width;

    document.body.classList.add('side-panel-resizing');
    resizeGrip.setPointerCapture(e.pointerId);
    resizeGrip.addEventListener('pointermove', onPointerMove);

    // The pointerup event might not be dispatched on the resizeGrip itself
    // (e.g. when the pointer is above/below the grip, or beyond the side panel's
    // minimum/maximum width), so listen for it on the document instead.
    document.addEventListener('pointerup', onPointerUp);
  });

  // Handle resizing with keyboard using a hidden range input.
  widthInput.addEventListener('change', (event) => {
    const { minWidth, range } = getSidePanelWidthStyles();
    const inputPercentage = parseInt(event.target.value, 10);
    const directedPercentage = getDirectedPercentage(inputPercentage);
    const newWidth = minWidth + (range * directedPercentage) / 100;
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
