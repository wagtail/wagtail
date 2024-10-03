import axe, { AxeResults, Spec } from 'axe-core';
import {
  sortAxeViolations,
  WagtailAxeConfiguration,
  addCustomChecks,
  checkImageAltText,
  getA11yReport,
} from './a11y-result';

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

describe('addCustomChecks', () => {
  it('should integrate custom checks into the Axe spec', () => {
    const spec: Spec = {
      checks: [{ id: 'check-id', evaluate: 'functionName' }],
      rules: [
        {
          id: 'rule-id',
          impact: 'serious',
          any: ['check-id'],
        },
      ],
    };
    const modifiedSpec = addCustomChecks(spec);
    const customCheck = modifiedSpec?.checks?.find(
      (check) => check.id === 'check-id',
    );
    expect(customCheck).toBeDefined();
    expect(customCheck?.evaluate).toBe('functionName');
  });

  it('should return spec unchanged if no custom checks match', () => {
    const spec: Spec = {
      checks: [{ id: 'non-existent-check', evaluate: '' }],
    };
    const modifiedSpec = addCustomChecks(spec);
    expect(modifiedSpec).toEqual(spec);
  });
});

// Options for checkImageAltText function
const options = {
  pattern: '\\.(avif|gif|jpg|jpeg|png|svg|webp)$|_',
};

describe.each`
  text                                                | result
  ${'Good alt text with words like GIFted and motif'} | ${true}
  ${'Bad alt text.png'}                               | ${false}
  ${'Bad_alt_text'}                                   | ${false}
  ${''}                                               | ${true}
`('checkImageAltText', ({ text, result }) => {
  const resultText = result ? 'should not be flagged' : 'should be flagged';
  test(`alt text: "${text}" ${resultText}`, () => {
    const image = document.createElement('img');
    image.setAttribute('alt', text);
    expect(checkImageAltText(image, options)).toBe(result);
  });
});

describe('checkImageAltText edge cases', () => {
  test('should not flag images with no alt attribute', () => {
    const image = document.createElement('img');
    expect(checkImageAltText(image, options)).toBe(true);
  });
});

jest.mock('axe-core', () => ({
  configure: jest.fn(),
  run: jest.fn(),
}));

describe('getA11yReport', () => {
  let consoleError: jest.SpyInstance;

  beforeEach(() => {
    consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    jest.clearAllMocks();
  });

  afterEach(() => {
    consoleError.mockRestore();
  });

  it('should configure Axe with custom rules and return the accessibility report', async () => {
    const mockResults = {
      violations: [
        {
          nodes: [{}, {}, {}], // 3 nodes with violations
        },
      ],
    };
    (axe.run as jest.Mock).mockResolvedValue(mockResults);
    const config: WagtailAxeConfiguration = {
      context: 'body',
      options: {},
      messages: {},
      spec: {
        checks: [{ id: 'check-image-alt-text', evaluate: '' }],
      },
    };
    const report = await getA11yReport(config);
    expect(axe.configure).toHaveBeenCalled();
    expect(consoleError).toHaveBeenCalledWith(
      'axe.run results',
      mockResults.violations,
    );
    expect(axe.run).toHaveBeenCalledWith(config.context, config.options);
    expect(report.results).toEqual(mockResults);
    expect(report.a11yErrorsNumber).toBe(3);
  });

  it('should return an accessibility report with zero errors if there are no violations', async () => {
    const mockResults = {
      violations: [],
    };
    (axe.run as jest.Mock).mockResolvedValue(mockResults);
    const config: WagtailAxeConfiguration = {
      context: 'body',
      options: {},
      messages: {},
      spec: {
        checks: [{ id: 'check-image-alt-text', evaluate: '' }],
      },
    };
    const report = await getA11yReport(config);
    expect(report.a11yErrorsNumber).toBe(0);
    expect(consoleError).not.toHaveBeenCalled();
  });
});
