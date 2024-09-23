/* global buildExpandingFormset */
import $ from 'jquery';

window.$ = $;

import './expanding-formset';

describe('buildExpandingFormset', () => {
  it('exposes module as global', () => {
    expect(window.buildExpandingFormset).toBeDefined();
  });
});
