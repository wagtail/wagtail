import {
  getFormat,
  gettext,
  gettextNoop,
  ngettext,
  pluralIdx,
} from './gettext';

const STRING =
  'The name wagtail stems from the constant sideways wagging of the tail.';

afterEach(() => {
  // clear any mocked globals after each test
  if (window.django) {
    delete window.django;
  }
});

describe('gettext', () => {
  it('should return the provided string if Django gettext is not loaded', () => {
    expect(gettext(STRING)).toEqual(STRING);
  });

  it('should call the global Django util if loaded', () => {
    const gettextMock = jest.fn();
    window.django = { gettext: gettextMock };
    gettext(STRING);
    expect(gettextMock).toHaveBeenCalledWith(STRING);
  });
});

describe('ngettext', () => {
  it('should emulate the Django ngettext function if it is not loaded', () => {
    expect(ngettext('One bird', 'Many birds', 1)).toEqual('One bird');
    expect(ngettext('One bird', 'Many birds', 2)).toEqual('Many birds');
  });

  it('should call the global Django util if loaded', () => {
    const ngettextMock = jest.fn();
    window.django = { ngettext: ngettextMock };
    ngettext('One bird', 'Many birds', 2);
    expect(ngettextMock).toHaveBeenCalledWith('One bird', 'Many birds', 2);
  });
});

describe('getFormat', () => {
  it('should return an empty string if Django get_format is not loaded', () => {
    expect(getFormat('FIRST_DAY_OF_WEEK')).toEqual('');
  });

  it('should call the global Django util if loaded', () => {
    const getFormatMock = jest.fn();
    window.django = { get_format: getFormatMock };
    getFormat('FIRST_DAY_OF_WEEK');
    expect(getFormatMock).toHaveBeenCalledWith('FIRST_DAY_OF_WEEK');
  });
});

describe('gettextNoop', () => {
  it('should return the provided string if Django gettext_noop is not loaded', () => {
    expect(gettextNoop(STRING)).toEqual(STRING);
  });

  it('should call the global Django util if loaded', () => {
    const gettextNoopMock = jest.fn();
    window.django = { gettext_noop: gettextNoopMock };
    gettextNoop(STRING);
    expect(gettextNoopMock).toHaveBeenCalledWith(STRING);
  });
});

describe('pluralIdx', () => {
  it('should return false if Django pluralidx is not loaded', () => {
    expect(pluralIdx(3)).toEqual(false);
  });

  it('should call the global Django util if loaded', () => {
    const pluralidxMock = jest.fn();
    window.django = { pluralidx: pluralidxMock };
    pluralIdx(5);
    expect(pluralidxMock).toHaveBeenCalledWith(5);
  });
});
