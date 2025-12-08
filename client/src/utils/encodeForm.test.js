/**
 * @jest-environment jsdom
 */

import { encodeForm } from './encodeForm';

describe('encodeForm utility', () => {
  it('encodes a simple form into URLSearchParams format', () => {
    const form = document.createElement('form');

    const titleInput = document.createElement('input');
    titleInput.name = 'title';
    titleInput.value = 'Hello';
    form.appendChild(titleInput);

    const countInput = document.createElement('input');
    countInput.name = 'count';
    countInput.value = '10';
    form.appendChild(countInput);

    const result = encodeForm(form);
    const params = new URLSearchParams(result);

    expect(params.get('title')).toBe('Hello');
    expect(params.get('count')).toBe('10');
  });

  it('supports multiple fields with the same name', () => {
    const form = document.createElement('form');

    const firstTagInput = document.createElement('input');
    firstTagInput.name = 'tag';
    firstTagInput.value = 'a';
    form.appendChild(firstTagInput);

    const secondTagInput = document.createElement('input');
    secondTagInput.name = 'tag';
    secondTagInput.value = 'b';
    form.appendChild(secondTagInput);

    const result = encodeForm(form);
    const params = new URLSearchParams(result);

    expect(params.getAll('tag')).toEqual(['a', 'b']);
  });
});
