import { Application } from '@hotwired/stimulus';
import { TooltipController } from './TooltipController';

describe('TooltipController', () => {
  let application;

  beforeEach(async () => {
    document.body.innerHTML = `
<section>
  <button
    type="button"
    id="tooltip-default"
    data-controller="w-tooltip"
    data-w-tooltip-content-value="Extra content"
  >
    CONTENT
  </button>
  <button
    id="tooltip-custom"
    type="button"
    data-controller="w-tooltip"
    data-w-tooltip-content-value="Tippy top content"
    data-w-tooltip-placement-value="top"
    data-action="custom:show->w-tooltip#show custom:hide->w-tooltip#hide"
  >
    CONTENT
  </button>
</section>`;

    application = Application.start();
    application.register('w-tooltip', TooltipController);

    await Promise.resolve();

    // set all animation durations to 0 so that tests can ignore animation delays
    // Tippy relies on transitionend which is not yet supported in JSDom
    // https://github.com/jsdom/jsdom/issues/1781

    document
      .querySelectorAll('[data-controller="w-tooltip"]')
      .forEach((element) => {
        application
          .getControllerForElementAndIdentifier(element, 'w-tooltip')
          .tippy.setProps({ duration: 0 }); // tippy will merge props with whatever has already been set
      });
  });

  afterEach(() => {
    application?.stop();
  });

  it('should create a tooltip when hovered & remove it when focus moves away', async () => {
    const tooltipTrigger = document.getElementById('tooltip-default');

    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(0);

    tooltipTrigger.dispatchEvent(new Event('mouseenter'));

    await Promise.resolve();

    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(1);
    const tooltip = document.querySelector('[role="tooltip"]');

    expect(tooltip).toBeTruthy();

    expect(tooltip.textContent).toEqual('Extra content');
    expect(tooltip.dataset.placement).toEqual('bottom'); // the default placement
  });

  it('should create a tooltip that accepts a different placement value', async () => {
    const tooltipTrigger = document.getElementById('tooltip-custom');

    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(0);

    tooltipTrigger.dispatchEvent(new Event('mouseenter'));

    await Promise.resolve();

    const tooltip = document.querySelector('[role="tooltip"]');

    expect(tooltip.textContent).toEqual('Tippy top content');
    expect(tooltip.dataset.placement).toEqual('top');
  });

  it('should destroy the tippy instance on disconnect', async () => {
    const tooltipTrigger = document.getElementById('tooltip-default');

    const controller = application.getControllerForElementAndIdentifier(
      tooltipTrigger,
      'w-tooltip',
    );

    expect(controller.tippy).toBeDefined();
    jest.spyOn(controller.tippy, 'destroy');
    expect(controller.tippy.destroy).not.toHaveBeenCalled();

    tooltipTrigger.removeAttribute('data-controller');

    await Promise.resolve();

    expect(controller.tippy.destroy).toHaveBeenCalled();
  });

  it('should support actions for show and hide', () => {
    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(0);

    const tooltipTrigger = document.getElementById('tooltip-custom');

    tooltipTrigger.dispatchEvent(new CustomEvent('custom:show'));

    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(1);

    tooltipTrigger.dispatchEvent(new CustomEvent('custom:hide'));

    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(0);
  });

  it('should keep content in sync with any data attribute changes', async () => {
    const tooltipTrigger = document.getElementById('tooltip-custom');

    expect(document.querySelectorAll('[role="tooltip"]')).toHaveLength(0);

    tooltipTrigger.dispatchEvent(new Event('mouseenter'));

    const tooltip = document.querySelector('[role="tooltip"]');

    expect(tooltip.textContent).toEqual('Tippy top content');

    // change the content value
    tooltipTrigger.setAttribute('data-w-tooltip-content-value', 'NEW content!');

    await Promise.resolve();

    expect(tooltip.textContent).toEqual('NEW content!');
  });

  it('should support passing the offset value', async () => {
    document.body.innerHTML = `
    <section>
      <button
        id="button"
        type="button"
        data-controller="w-tooltip"
        data-w-tooltip-offset-value="[10, 20]"
      >
        CONTENT
      </button>
    </section>`;

    await Promise.resolve(requestAnimationFrame);

    const tippy = application.getControllerForElementAndIdentifier(
      document.getElementById('button'),
      'w-tooltip',
    ).tippy;

    expect(tippy.props).toHaveProperty('offset', [10, 20]);
  });
});
