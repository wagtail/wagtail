import { domReady } from './domReady';

jest.useFakeTimers();

describe('domReady', () => {
  it('should resolve as true if the DOM is not in loading state', () => {
    expect(document.readyState).toEqual('complete');

    return domReady().then(() => {
      expect(document.readyState).toEqual('complete');
    });
  });

  it('should resolve as true if the DOM loading but then completes loading', () => {
    let trackingValue = null;

    Object.defineProperty(document, 'readyState', {
      value: 'loading',
    });

    expect(document.readyState).toEqual('loading');

    setTimeout(() => {
      trackingValue = true;
      document.dispatchEvent(new CustomEvent('DOMContentLoaded'));
    }, 5);

    const promise = domReady();

    jest.runAllTimers();

    return promise.then(() => {
      expect(trackingValue).toEqual(true);
    });
  });
});
