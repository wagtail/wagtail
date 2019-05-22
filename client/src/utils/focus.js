const OUTLINE_ON = 'focus-outline-on';
const OUTLINE_OFF = 'focus-outline-off';

const toggleFocusOutline = (isOn) => {
  document.body.classList.toggle(OUTLINE_OFF, !isOn);
  document.body.classList.toggle(OUTLINE_ON, isOn);
};

const removeFocusOutline = toggleFocusOutline.bind(null, false);
const addFocusOutline = toggleFocusOutline.bind(null, true);

/**
 * Adds a heavy focus outline to the UI, only for users who tab through the page.
 * The outline is not useful with touch or mouse input – these remove the outline.
 */
export const initFocusOutline = () => {
  // Focus outline styles are added by default in the HTML, so they work without JS enabled.
  removeFocusOutline();

  window.addEventListener('mousedown', removeFocusOutline);
  window.addEventListener('touchstart', removeFocusOutline);

  window.addEventListener('keydown', e => {
    const isTabKey = e.keyCode === 9;

    if (isTabKey) {
      addFocusOutline();
    }
  });
};
