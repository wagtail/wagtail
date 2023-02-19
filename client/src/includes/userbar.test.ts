import { AxeResults } from 'axe-core';
import { sortAxeViolations } from './userbar';

const mockDocument = `
<div id="a"></div>
<div id="b"></div>
<div id="c"></div>
<div id="d"></div>
`;

// Multiple selectors per violation, multiple violations per selector
const mockViolations = {
  a: { id: 'axe-1', nodes: [{ target: ['#d'] }, { target: ['#a'] }] },
  b: { id: 'axe-2', nodes: [{ target: ['#d'] }, { target: ['#b'] }] },
  c: { id: 'axe-3', nodes: [{ target: ['#c'] }] },
};

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
    mockViolations.a,
    mockViolations.b,
    mockViolations.c,
  ] as AxeResults['violations'];
  expect(sortAxeViolations(violations)).toEqual([
    mockViolations.a,
    mockViolations.b,
    mockViolations.c,
  ]);
});

it('changes the order to match the DOM', () => {
  document.body.innerHTML = mockDocument;
  const violations = [
    mockViolations.c,
    mockViolations.b,
    mockViolations.a,
  ] as AxeResults['violations'];
  expect(sortAxeViolations(violations)).toEqual([
    mockViolations.a,
    mockViolations.b,
    mockViolations.c,
  ]);
});
