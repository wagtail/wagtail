import { AxeResults } from 'axe-core';
import { sortAxeViolations, checkImageAltText } from './a11y-result';

const mockDocument = `
<div id="a"></div>
<div id="b"></div>
<div id="c"></div>
<div id="d"></div>
`;

// Multiple selectors per violation, multiple violations per selector
const mockViolations = {
  da: { id: 'axe-1', nodes: [{ target: ['#d'] }, { target: ['#a'] }] },
  db: { id: 'axe-2', nodes: [{ target: ['#d'] }, { target: ['#b'] }] },
  third: { id: 'axe-3', nodes: [{ target: ['#c'] }] },
};

describe('sortAxeViolations', () => {
  it('works with no nodes', () => {
    const violations = [
      { id: 'axe-1', nodes: [] },
      { id: 'axe-2', nodes: [] },
    ] as unknown as AxeResults['violations'];
    expect(sortAxeViolations(violations)).toEqual([
      { id: 'axe-1', nodes: [] },
      { id: 'axe-2', nodes: [] },
    ]);
  });

  it('preserves the existing order if correct', () => {
    document.body.innerHTML = mockDocument;
    const violations = [
      mockViolations.da,
      mockViolations.db,
      mockViolations.third,
    ] as AxeResults['violations'];
    expect(sortAxeViolations(violations)).toEqual([
      mockViolations.da,
      mockViolations.db,
      mockViolations.third,
    ]);
  });

  it('changes the order to match the DOM', () => {
    document.body.innerHTML = mockDocument;
    const violations = [
      mockViolations.third,
      mockViolations.db,
      mockViolations.da,
    ] as AxeResults['violations'];
    expect(sortAxeViolations(violations)).toEqual([
      mockViolations.da,
      mockViolations.db,
      mockViolations.third,
    ]);
  });
});

describe('checkImageAltText', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <img src="image1.jpg" alt="Good alt text with words like GIFted and moTIF">
      <img src="image2.png" alt="Bad alt text.png">
      <img src="image3.tiff" alt="Bad alt text.TIFF more text">
      <img src="image4.png" alt="https://Bad.alt.text">
      <img src="https://example.com/image5.gif" alt="">
      <img src="image6.jpg">
    `;
  });

  it('should not flag images with good alt text', () => {
    const image = document.querySelector<HTMLImageElement>(
      'img[src="image1.jpg"]',
    );
    if (!image) return;
    expect(checkImageAltText(image)).toBe(true);
  });

  it('should flag images with a file extension in the alt text', () => {
    const image = document.querySelector<HTMLImageElement>(
      'img[src="image2.png"]',
    );
    if (!image) return;
    expect(checkImageAltText(image)).toBe(false);
  });

  it('should flag images with a capitalised file extension in the alt text', () => {
    const image = document.querySelector<HTMLImageElement>(
      'img[src="image3.tiff"]',
    );
    if (!image) return;
    expect(checkImageAltText(image)).toBe(false);
  });

  it('should flag images with a file URL in the alt text', () => {
    const image = document.querySelector<HTMLImageElement>(
      'img[src="image4.png"]',
    );
    if (!image) return;
    expect(checkImageAltText(image)).toBe(false);
  });

  it('should not flag images with empty alt attribute', () => {
    const image = document.querySelector<HTMLImageElement>(
      'img[src="https://example.com/image5.gif"]',
    );
    if (!image) return;
    expect(checkImageAltText(image)).toBe(true);
  });

  it('should not flag images with no alt attribute', () => {
    const image = document.querySelector<HTMLImageElement>(
      'img[src="image6.jpg"]',
    );
    if (!image) return;
    expect(checkImageAltText(image)).toBe(true);
  });
});
