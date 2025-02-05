import { Application } from '@hotwired/stimulus';
import { CountController } from './CountController';

describe('CountController', () => {
  let application;

  describe('basic behavior', () => {
    beforeAll(() => {
      application?.stop();

      document.body.innerHTML = `
  <section>
    <div id="element" data-controller="w-count" data-action="recount@document->w-count#count">
      <span id="total" data-w-count-target="total"></span>
      <span id="label" data-w-count-target="label"></span>
    </div>
    <ul id="items"></ul>
  </section>`;

      application = Application.start();
      application.register('w-count', CountController);
    });

    it('should run the count on connect', () => {
      expect(
        document.getElementById('element').dataset.wCountTotalValue,
      ).toEqual('0');
    });

    it('should count the items if present', async () => {
      document.getElementById('items').innerHTML = `
      <li class="error-message"></li>
      <li class="help-critical"></li>
      <li class="error-message"></li>`;

      document.dispatchEvent(new CustomEvent('recount'));
      await Promise.resolve();

      expect(
        document.getElementById('element').dataset.wCountTotalValue,
      ).toEqual('3');
      expect(document.getElementById('total').innerHTML).toEqual('3');
      expect(document.getElementById('label').innerHTML).toEqual('3 errors');
    });

    it('should update the targets based on the min value set', async () => {
      document.getElementById('element').dataset.wCountMinValue = '3';

      await Promise.resolve();

      expect(document.getElementById('total').innerHTML).toEqual('');
      expect(document.getElementById('label').innerHTML).toEqual('');
    });

    it('should support a custom find value for different elements', async () => {
      document.getElementById('items').innerHTML = `
      <li class="count-me"></li>
      <li class="count-me"></li>
      <li class="count-me"></li>
      <li id="me-also"></li>`;

      document.getElementById('element').dataset.wCountFindValue =
        '.count-me,#me-also';

      document.dispatchEvent(new CustomEvent('recount'));
      await Promise.resolve();

      expect(document.getElementById('total').innerHTML).toEqual('4');
      expect(document.getElementById('label').innerHTML).toEqual('4 errors');
    });

    it('should support a custom translation labels value', async () => {
      document.getElementById('element').dataset.wCountLabelsValue =
        JSON.stringify(['One __total__', '__total__ items']);
      document.getElementById('element').dataset.wCountMinValue = '0';

      document.dispatchEvent(new CustomEvent('recount'));
      await Promise.resolve();

      expect(document.getElementById('label').innerHTML).toEqual('4 items');
    });
  });

  describe('when one item exists in specified container', () => {
    beforeAll(() => {
      application?.stop();

      document.body.innerHTML = `
  <section>
    <div class="w-tabs__errors" data-controller="w-count" data-w-count-active-class="!w-flex" data-w-count-container-value="#tab">
      <span id="total" data-w-count-target="total"></span>
      <span id="label" data-w-count-target="label"></span>
    </div>
    <div id="tab"></div>
  </section>`;

      application = Application.start();
      application.register('w-count', CountController);
    });

    it('should count the errors if one exists', () => {
      expect(document.getElementById('total').innerHTML).toEqual('');
      expect(document.getElementById('label').innerHTML).toEqual('');
      expect(
        document.querySelector('.w-tabs__errors').classList.contains('!w-flex'),
      ).toBe(false);
    });
  });

  describe('when one item exists in specified container', () => {
    beforeAll(() => {
      application?.stop();

      document.body.innerHTML = `
  <section>
    <div class="w-tabs__errors" data-controller="w-count" data-w-count-active-class="!w-flex" data-w-count-container-value="#tab">
      <span id="total" data-w-count-target="total"></span>
      <span id="label" data-w-count-target="label"></span>
    </div>
    <div id="tab"><div class="error-message"></div></div>
  </section>`;

      application = Application.start();
      application.register('w-count', CountController);
    });

    it('should count the errors if one exists', () => {
      expect(document.getElementById('total').innerHTML).toEqual('1');
      expect(document.getElementById('label').innerHTML).toEqual('1 error');
      expect(
        document.querySelector('.w-tabs__errors').classList.contains('!w-flex'),
      ).toBe(true);
    });
  });

  describe('when more than one item exists in specified container', () => {
    beforeAll(() => {
      application?.stop();

      document.body.innerHTML = `
  <section>
    <div class="w-tabs__errors" data-controller="w-count" data-w-count-active-class="!w-flex" data-w-count-container-value="#tab">
      <span id="total" data-w-count-target="total"></span>
      <span id="label" data-w-count-target="label"></span>
    </div>
    <div id="tab">
      <div class="error-message"></div>
      <div class="error-message"></div>
      <span class="help-critical"></span>
    </div>
  </section>`;

      application = Application.start();
      application.register('w-count', CountController);
    });

    it('should count the errors if one exists', () => {
      expect(document.getElementById('total').innerHTML).toEqual('3');
      expect(document.getElementById('label').innerHTML).toEqual('3 errors');
      expect(
        document.querySelector('.w-tabs__errors').classList.contains('!w-flex'),
      ).toBe(true);
    });
  });
});
