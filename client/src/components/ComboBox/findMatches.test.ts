import findMatches, { contains } from './findMatches';

describe('findMatches', () => {
  describe.each`
    label                           | string    | substring   | result
    ${'full match'}                 | ${'abcä'} | ${'abcä'}   | ${true}
    ${'start match'}                | ${'abcä'} | ${'ab'}     | ${true}
    ${'end match'}                  | ${'abcä'} | ${'cä'}     | ${true}
    ${'base full match'}            | ${'abcä'} | ${'abca'}   | ${true}
    ${'base partial match'}         | ${'abcä'} | ${'ca'}     | ${true}
    ${'base full match reverse'}    | ${'abca'} | ${'abcä'}   | ${true}
    ${'base partial match reverse'} | ${'abca'} | ${'cä'}     | ${true}
    ${'no match'}                   | ${'abcä'} | ${'potato'} | ${false}
  `('contains', ({ label, string, substring, result }) => {
    test(label, () => {
      expect(contains(string, substring)).toBe(result);
    });
  });

  const findMatchesItems = [
    { label: 'label', desc: '' },
    { label: '', desc: 'description' },
    { label: 'abcä', desc: 'abcä' },
    { label: 'abca', desc: 'abca' },
    { label: 'ab', desc: 'ab' },
    { label: null, desc: null },
    { label: undefined, desc: undefined },
  ];

  describe.each`
    label                 | input            | results
    ${'one match label'}  | ${'label'}       | ${[0]}
    ${'one match desc'}   | ${'description'} | ${[1]}
    ${'multiple matches'} | ${'ab'}          | ${[2, 3, 4]}
    ${'base match'}       | ${'ca'}          | ${[2, 3]}
  `('findMatches', ({ label, input, results }) => {
    test(label, () => {
      const getSearchFields = (i) => [i.label, i.desc];
      expect(findMatches(findMatchesItems, getSearchFields, input)).toEqual(
        expect.arrayContaining(results.map((i) => findMatchesItems[i])),
      );
    });
  });
});
