import { initIconSprite } from './initIconSprite';

describe('initIconSprite', () => {
  const spriteURL = 'https://example.com/sprite.svg';
  const responseText = '<svg>...</svg>';

  beforeEach(() => {
    global.fetch = jest.fn();
    document.body.innerHTML = `<div data-sprite></div>`;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should insert the response text into the spriteContainer', async () => {
    const spriteContainer = document.querySelector('[data-sprite]');

    global.fetch.mockResolvedValue({
      text: () => Promise.resolve(responseText),
    });
    initIconSprite(spriteContainer, spriteURL);
    await new Promise(requestAnimationFrame);

    expect(global.fetch).toHaveBeenCalled();
    expect(global.fetch).toHaveBeenCalledWith(spriteURL);
    expect(spriteContainer.innerHTML).toEqual(responseText);
  });

  it('should store the response text in localStorage', async () => {
    const spriteContainer = document.querySelector('[data-sprite]');

    jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {});

    global.fetch.mockResolvedValue({
      text: () => Promise.resolve(responseText),
    });
    initIconSprite(spriteContainer, spriteURL);
    await new Promise(requestAnimationFrame);

    expect(localStorage).not.toBe(null);
    expect(localStorage['wagtail:spriteData']).toBe(responseText);
    expect(localStorage['wagtail:spriteRevision']).toBe(spriteURL);
  });

  it('should throw an error if the fetch fails', async () => {
    const spriteContainer = document.querySelector('[data-sprite]');
    global.fetch.mockRejectedValue('Fetch failed');
    const spy = jest.spyOn(console, 'error').mockImplementation();

    initIconSprite(spriteContainer, spriteURL);
    await new Promise(requestAnimationFrame);

    expect(global.fetch).toHaveBeenCalled();
    expect(global.fetch).toHaveBeenCalledWith(spriteURL);
    expect(spy).toHaveBeenCalledWith(
      `Error fetching ${spriteURL}. Error: Fetch failed`,
    );
  });
});
