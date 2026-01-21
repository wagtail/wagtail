import { encodeForm } from './encodeForm';

describe('encodeForm', () => {
  it('encodes standard text fields', () => {
    const form = document.createElement('form');
    form.innerHTML = `
      <input type="text" name="username" value="wagtail">
      <input type="text" name="role" value="developer">
    `;
    expect(encodeForm(form)).toBe('username=wagtail&role=developer');
  });

  it('encodes multiple values for the same name', () => {
    const form = document.createElement('form');
    form.innerHTML = `
      <input type="checkbox" name="features" value="cms" checked>
      <input type="checkbox" name="features" value="ecommerce" checked>
    `;
    expect(encodeForm(form)).toBe('features=cms&features=ecommerce');
  });

  it('encodes file inputs by their filename (legacy behavior)', () => {
    const form = document.createElement('form');
    // In JSDOM/Browser, an empty file input results in a File object with an empty name
    form.innerHTML = '<input type="file" name="upload">';
    expect(encodeForm(form)).toBe('upload=');
  });

  it('handles empty forms', () => {
    const form = document.createElement('form');
    expect(encodeForm(form)).toBe('');
  });
});
