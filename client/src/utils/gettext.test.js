import {
  getFormat,
  gettext,
  gettextNoop,
  ngettext,
  pluralIdx,
} from './gettext';

const STRING =
  'The name wagtail stems from the constant sideways wagging of the tail.';

describe('gettext', () => {
  beforeEach(() => {
    window.django = { gettext: jest.fn((val) => val) };
  });

  it('should return the value based on the django util', () => {
    expect(window.django.gettext).not.toHaveBeenCalled();
    expect(gettext(STRING)).toEqual(STRING);
    expect(window.django.gettext).toHaveBeenCalledWith(STRING);
  });
});

describe('ngettext', () => {
  beforeEach(() => {
    window.django = { ngettext: jest.fn((val) => val) };
  });

  it('should return the value based on the django util', () => {
    expect(window.django.ngettext).not.toHaveBeenCalled();
    expect(ngettext('One bird', 'Many birds', 2)).toEqual('One bird');
    expect(window.django.ngettext).toHaveBeenCalledWith(
      'One bird',
      'Many birds',
      2,
    );
  });
});

describe('getFormat', () => {
  beforeEach(() => {
    window.django = { get_format: jest.fn(() => 1) };
  });

  it('should return the value based on the django util', () => {
    expect(window.django.get_format).not.toHaveBeenCalled();
    expect(getFormat('FIRST_DAY_OF_WEEK')).toEqual(1);
    expect(window.django.get_format).toHaveBeenCalledWith('FIRST_DAY_OF_WEEK');
  });
});

describe('gettextNoop', () => {
  beforeEach(() => {
    window.django = { gettext_noop: jest.fn((val) => val) };
  });

  it('should return the value based on the django util', () => {
    expect(window.django.gettext_noop).not.toHaveBeenCalled();
    expect(gettextNoop(STRING)).toEqual(STRING);
    expect(window.django.gettext_noop).toHaveBeenCalledWith(STRING);
  });
});

describe('pluralIdx', () => {
  beforeEach(() => {
    window.django = {
      pluralidx: jest.fn((val) => ({ 0: true, 1: false }[val] || true)),
    };
  });

  it('should return the value based on the django util', () => {
    expect(window.django.pluralidx).not.toHaveBeenCalled();
    expect(pluralIdx(0)).toEqual(true);
    expect(window.django.pluralidx).toHaveBeenCalledWith(0);
  });
});
