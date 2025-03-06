const inlinePanelInstances = new Map();

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll("[id$='-FORMS']").forEach((panelElement) => {
    const panel = new window.InlinePanel({
      formsetPrefix: panelElement.dataset.formsetPrefix,
      emptyChildFormPrefix: panelElement.dataset.emptyChildFormPrefix,
      canOrder: panelElement.dataset.canOrder === 'true',
      maxForms: parseInt(panelElement.dataset.maxForms, 10),
    });

    inlinePanelInstances.set(panelElement, panel);
  });
});
