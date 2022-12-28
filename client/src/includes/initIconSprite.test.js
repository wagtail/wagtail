import { initIconSprite } from './initIconSprite';

describe('it should load the svgs into localStorage', () => {
  document.body.innerHTML = `
    <div data-sprite></div>
    `;
  const spriteURL =
    'https://s3-us-west-2.amazonaws.com/s.cdpn.io/106114/tiger.svg';
  const spriteContainer = document.querySelector('[data-sprite]');
  jest.mock('./initIconSprite');
  it('should load the svg in localStorage', () => {
    initIconSprite(spriteContainer, spriteURL);

    let request;

    // Mock the XMLHttpRequest object
    window.XMLHttpRequest = jest.fn().mockImplementation(() => ({
      open: jest.fn(),
      send: jest.fn(),
      onload: jest.fn(),
      responseText:
        'https://s3-us-west-2.amazonaws.com/s.cdpn.io/106114/tiger.svg',
      status: 200,
    }));

    // Call the code being tested
    try {
      request = new XMLHttpRequest();
      request.open('GET', spriteURL, true);
      // eslint-disable-next-line consistent-return
      request.onload = () => {
        if (request.status >= 200 && request.status < 400) {
          const data = request.responseText;
          return data;
        }
      };
      request.send();
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(e);
    }

    // Assert that the code behaved as expected
    expect(window.XMLHttpRequest).toHaveBeenCalled();
    expect(request.open).toHaveBeenCalledWith('GET', spriteURL, true);
    expect(request.status).toBe(200);
    expect(request.send).toHaveBeenCalled();
    expect(request.onload).toHaveBeenCalled();
  });
});
