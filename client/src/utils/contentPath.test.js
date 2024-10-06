import {
  getWagtailDirectives,
  getContentPathSelector,
  getElementByContentPath,
} from './contentPath';

describe('getWagtailDirectives', () => {
  afterEach(() => {
    window.location.hash = '';
  });

  it('should return the directive after the delimiter as-is', () => {
    window.location.hash = '#:w:contentpath=abc1.d2e.3f';
    expect(getWagtailDirectives()).toEqual('contentpath=abc1.d2e.3f');
  });

  it('should allow a normal anchor in front of the delimiter', () => {
    window.location.hash = '#an-anchor:w:contentpath=abc1.d2e.3f';
    expect(getWagtailDirectives()).toEqual('contentpath=abc1.d2e.3f');
  });

  it('should allow multiple values for the same directive', () => {
    window.location.hash =
      '#hello:w:contentpath=abc1.d2e.3f&unknown=123&unknown=456';
    expect(getWagtailDirectives()).toEqual(
      'contentpath=abc1.d2e.3f&unknown=123&unknown=456',
    );
  });
});

describe('getContentPathSelector', () => {
  it('should return a selector string for a single content path', () => {
    expect(getContentPathSelector('abc1')).toEqual('[data-contentpath="abc1"]');
  });
  it('should allow dotted content path', () => {
    expect(getContentPathSelector('abc1.d2e.3f')).toEqual(
      '[data-contentpath="abc1"] [data-contentpath="d2e"] [data-contentpath="3f"]',
    );
  });

  it('should ignore leading, trailing, and extra dots', () => {
    expect(getContentPathSelector('.abc1...d2e..3f.')).toEqual(
      '[data-contentpath="abc1"] [data-contentpath="d2e"] [data-contentpath="3f"]',
    );
  });

  it('should return an empty string if content path is an empty string', () => {
    expect(getContentPathSelector('')).toEqual('');
  });
});

describe('getElementByContentPath', () => {
  beforeEach(() => {
    document.body.innerHTML = /* html */ `
      <div id="one" data-contentpath="abc1">
        <div id="two" data-contentpath="d2e">
          <div id="three" data-contentpath="3f"></div>
        </div>
        <div id="four" data-contentpath="g4h"></div>
      </div>
    `;
  });

  afterEach(() => {
    window.location.hash = '';
  });

  it('should return the element for a single content path', () => {
    const element = getElementByContentPath('abc1');
    expect(element).toBeTruthy();
    expect(element.id).toEqual('one');
  });

  it('should return the element for a dotted content path', () => {
    const element = getElementByContentPath('abc1.d2e.3f');
    expect(element).toBeTruthy();
    expect(element.id).toEqual('three');
  });

  it('should read from the contentpath directive if there is one', () => {
    window.location.hash = '#:w:contentpath=abc1.d2e.3f';
    const element = getElementByContentPath();
    expect(element).toBeTruthy();
    expect(element.id).toEqual('three');
  });

  it('should return null if it cannot find the element', () => {
    expect(getElementByContentPath('abc1.d2e.3f.g4h')).toBeNull();
    expect(getElementByContentPath()).toBeNull();
  });
});
