import $ from 'jquery';

window.$ = $;

import { initTagField } from './TagController';

describe('initTagField', () => {
  let element;

  const tagitMock = jest.fn(function tagitMockInner() {
    element = this;
  });

  window.$.fn.tagit = tagitMock;

  beforeEach(() => {
    element = null;
    jest.clearAllMocks();
  });

  it('should not call jQuery tagit if the element is not found', () => {
    expect(tagitMock).not.toHaveBeenCalled();

    initTagField('not-present');

    expect(tagitMock).not.toHaveBeenCalled();
  });

  it('should call jQuery tagit if the element is found', () => {
    expect(tagitMock).not.toHaveBeenCalled();

    document.body.innerHTML = `
    <main>
      <input id="tag-input" type="text" value="abc" />
    </main>
    `;

    initTagField('tag-input', '/path/to/autocomplete/', {
      someOther: 'option',
    });

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
});
