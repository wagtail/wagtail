import $ from 'jquery';
import { InlinePanel } from '../../components/InlinePanel';
import { MultipleChooserPanel } from '../../components/MultipleChooserPanel';

window.InlinePanel = InlinePanel;
window.MultipleChooserPanel = MultipleChooserPanel;

function initKeyboardShortcuts() {
  // eslint-disable-next-line no-undef
  Mousetrap.bind(['mod+p'], () => {
    const previewToggle = document.querySelector(
      '[data-side-panel-toggle="preview"]',
    );
    if (previewToggle) previewToggle.click();
    return false;
  });

  // eslint-disable-next-line no-undef
  Mousetrap.bind(['mod+s'], () => {
    $('.action-save').trigger('click');
    return false;
  });
}

window.initKeyboardShortcuts = initKeyboardShortcuts;

$(() => {
  initKeyboardShortcuts();
});
