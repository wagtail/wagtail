import $ from 'jquery';

import { Application } from '@hotwired/stimulus';
import { TagController } from './TagController';

window.$ = $;

describe('TagController', () => {
  let application;
  let element;

  const tagitMock = jest.fn(function innerFunction() {
    element = this;
  });

  window.$.fn.tagit = tagitMock;

  element = null;

  beforeEach(() => {
    element = null;
    jest.clearAllMocks();
  });

  it('should create a global initTagField to call jQuery tagit if the element is found', async () => {
    expect(window.initTagField).toBeUndefined();
    expect(tagitMock).not.toHaveBeenCalled();

    application = Application.start();
    application.register('w-tag', TagController);

    document.body.innerHTML = `
    <main>
      <input id="tag-input" type="text" value="abc" />
    </main>`;

    window.initTagField('tag-input', '/path/to/autocomplete/', {
      someOther: 'option',
    });

    await new Promise(requestAnimationFrame);

    // check the jQuery instance is the correct element
    expect(element).toContain(document.getElementById('tag-input'));

    // check the tagit util was called correctly with supplied params
    expect(tagitMock).toHaveBeenCalledWith(
      expect.objectContaining({
        autocomplete: { source: '/path/to/autocomplete/' },
        someOther: 'option',
      }),
    );

    // check the supplied preprocessTag function
    const [{ preprocessTag }] = tagitMock.mock.calls[0];

    expect(preprocessTag).toBeInstanceOf(Function);

    expect(preprocessTag()).toEqual();
    expect(preprocessTag('"flat white"')).toEqual(`"flat white"`);
    expect(preprocessTag("'long black'")).toEqual(`"'long black'"`);
  });

  it('should not call jQuery tagit if the element is not found', async () => {
    expect(tagitMock).not.toHaveBeenCalled();

    window.initTagField('not-present');

    await new Promise(requestAnimationFrame);

    expect(tagitMock).not.toHaveBeenCalled();
  });

  it('should attach the jQuery tagit to the controlled element', async () => {
    document.body.innerHTML = `
  <form id="form">
    <input
      id="id_tags"
      type="text"
      name="tags"
      data-controller="w-tag"
      data-action="example:event->w-tag#clear"
      data-w-tag-options-value="{&quot;allowSpaces&quot;:true,&quot;tagLimit&quot;:10}"
      data-w-tag-url-value="/admin/tag-autocomplete/"
    >
  </form>`;

    expect(tagitMock).not.toHaveBeenCalled();

    await new Promise(requestAnimationFrame);

    expect(tagitMock).toHaveBeenCalledWith({
      allowSpaces: true,
      autocomplete: { source: '/admin/tag-autocomplete/' },
      preprocessTag: expect.any(Function),
      tagLimit: 10,
    });

    expect(element[0]).toEqual(document.getElementById('id_tags'));

    // check the supplied preprocessTag function
    const [{ preprocessTag }] = tagitMock.mock.calls[0];

    expect(preprocessTag).toBeInstanceOf(Function);

    expect(preprocessTag()).toEqual();
    expect(preprocessTag('"flat white"')).toEqual(`"flat white"`);
    expect(preprocessTag("'long black'")).toEqual(`"'long black'"`);
    expect(preprocessTag('caffe latte')).toEqual(`"caffe latte"`);

    // check the custom clear behaviour
    document
      .getElementById('id_tags')
      .dispatchEvent(new CustomEvent('example:event'));

    await new Promise(requestAnimationFrame);

    expect(tagitMock).toHaveBeenCalledWith('removeAll');
  });
});
