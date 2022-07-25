/**
 * Make panels collapsible, and collapse panels already marked as `collapsed`.
 */
export function initCollapsiblePanels() {
  const toggles = document.querySelectorAll<HTMLButtonElement>(
    '[data-panel-toggle]',
  );

  toggles.forEach((toggle) => {
    const panel = toggle.closest<HTMLElement>('[data-panel]');
    const content = document.querySelector<HTMLDivElement>(
      `#${toggle.getAttribute('aria-controls')}`,
    );

    if (!content || !panel) {
      return;
    }

    const onAnimationComplete = () => {
      content.dispatchEvent(
        new CustomEvent('commentAnchorVisibilityChange', { bubbles: true }),
      );
    };

    const hasCollapsed = panel.classList.contains('collapsed');
    const hasError = content.querySelector('[aria-invalid="true"]');

    // Collapse panels marked as `collapsed`, unless they contain invalid fields.
    if (hasCollapsed && !hasError) {
      // Use experimental `until-found` value.
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      content.hidden = 'until-found';
      toggle.setAttribute('aria-expanded', 'false');
      onAnimationComplete();
    }

    toggle.addEventListener('click', () => {
      const wasExpanded = toggle.getAttribute('aria-expanded') === 'true';
      const isExpanded = !wasExpanded;
      // Use experimental `until-found` value, so users can search inside the panels.
      // Browsers without support for `until-found` will ignore the value.
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      content.hidden = !isExpanded ? 'until-found' : '';
      onAnimationComplete();

      toggle.setAttribute('aria-expanded', `${isExpanded}`);
    });

    // Set the toggle back to expanded upon reveal.
    content.addEventListener('beforematch', () => {
      toggle.setAttribute('aria-expanded', 'true');
    });
  });
}

/**
 * Smooth scroll onto any active panel.
 * Needs to run after the whole page is loaded so the browser can resolve any
 * JS-driven :target.
 */
export function initAnchoredPanels() {
  const anchorTarget = document.querySelector('[data-panel]:target');
  if (anchorTarget) {
    anchorTarget.scrollIntoView({ behavior: 'smooth' });
  }
}
