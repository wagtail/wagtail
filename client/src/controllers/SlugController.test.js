import { Application } from '@hotwired/stimulus';
import { SlugController } from './SlugController';

describe('SlugController', () => {
  let application;

  beforeEach(() => {
    application?.stop();

    document.body.innerHTML = `
    <input
      id="id_slug"
      name="slug"
      type="text"
      data-controller="w-slug"
      data-action="blur->w-slug#slugify"
    />`;

    application = Application.start();
    application.register('w-slug', SlugController);
  });

  it('should trim and slugify the input value when focus is moved away from it', () => {
    const slugInput = document.querySelector('#id_slug');
    slugInput.value = '    slug  testing on     edit page ';

    slugInput.dispatchEvent(new CustomEvent('blur'));

    expect(document.querySelector('#id_slug').value).toEqual(
      'slug-testing-on-edit-page',
    );
  });

  it('should not allow unicode characters by default', () => {
    const slugInput = document.querySelector('#id_slug');

    expect(
      slugInput.hasAttribute('data-w-slug-allow-unicode-value'),
    ).toBeFalsy();

    slugInput.value = 'Visiter Toulouse en été 2025';

    slugInput.dispatchEvent(new CustomEvent('blur'));

    expect(slugInput.value).toEqual('visiter-toulouse-en-t-2025');
  });

  it('should now allow unicode characters by default', () => {
    const slugInput = document.querySelector('#id_slug');
    slugInput.setAttribute('data-w-slug-allow-unicode-value', 'true');

    expect(
      slugInput.hasAttribute('data-w-slug-allow-unicode-value'),
    ).toBeTruthy();

    slugInput.value = 'Visiter Toulouse en été 2025';

    slugInput.dispatchEvent(new CustomEvent('blur'));

    expect(slugInput.value).toEqual('visiter-toulouse-en-été-2025');
  });
});
