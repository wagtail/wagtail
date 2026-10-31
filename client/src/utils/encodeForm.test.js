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

  it('excludes file inputs', () => {
    const form = document.createElement('form');
    form.innerHTML = `
      <input type="file" name="upload">
      <input type="text" name="title" value="wagtail">
    `;
    expect(encodeForm(form)).toBe('title=wagtail');
  });

  it('handles empty forms', () => {
    const form = document.createElement('form');
    expect(encodeForm(form)).toBe('');
  });
});
