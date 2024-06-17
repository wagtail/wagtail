import { getContentMetrics } from './contentMetrics';

describe('getContentMetrics', () => {
  it('should return correct wordCount and readingTime using Intl.Segmenter', () => {
    const result = getContentMetrics('en-US', 'This is a test sentence.');
    expect(result.wordCount).toBe(5);
    expect(result.readingTime).toBe(0);
  });

  it('should handle empty text', () => {
    const result = getContentMetrics('en-US', '');
    expect(result.wordCount).toBe(0);
    expect(result.readingTime).toBe(0);
  });

  it('should handle text with punctuation correctly', () => {
    const text = `This is a longer text to test the word count and reading time calculation!
    Bread is a staple food prepared from a dough of flour and water; usually by baking.
    Throughout recorded history it has been popular around the world and is one of the
    oldest artificial foods: having been of importance since the dawn of agriculture.
    Proportions of types of flour and other ingredients vary widely? as do modes of preparation.
    As a result, types, shapes, sizes, and textures of breads differ around the world.
    Bread may be leavened by processes such as reliance on naturally occurring sourdough
    microbes, chemicals, industrially produced yeast, or high-pressure aeration...
    Some breads are baked before they have a chance to rise, often for traditional
    or religious reasons. Inclusions like fruits; nuts, and fats are sometimes added.
    Commercial bread typically includes additives to enhance flavor, texture, color,
    longevity, and production efficiency!
   `;
    const result = getContentMetrics('en-US', text);
    expect(result.wordCount).toBe(148);
    expect(result.readingTime).toBe(1);
  });

  it('should return integers for wordCount and readingTime', () => {
    const text = 'Yet another text';
    const result = getContentMetrics('en-US', text);
    expect(Number.isInteger(result.wordCount)).toBe(true);
    expect(Number.isInteger(result.readingTime)).toBe(true);
  });
});
