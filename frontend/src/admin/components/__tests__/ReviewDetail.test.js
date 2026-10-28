import { toChatCitations } from '../ReviewDetail';

const cite = (extra = {}) => ({
  sourceSlug: 'ley',
  sourceTitle: 'Ley',
  article: '1',
  fraction: null,
  page: 2,
  url: 'https://x.mx/l.pdf',
  ...extra,
});

describe('toChatCitations', () => {
  test('uses the stored n and orden, even with repeated and out-of-order markers', () => {
    const answer = 'Primero [3], luego [1] y otra vez [3].';
    const result = toChatCitations(answer, [cite({ n: 3, orden: 1 }), cite({ n: 1, orden: 2 })]);
    expect(result.map((c) => [c.n, c.orden])).toEqual([
      [3, 1],
      [1, 2],
    ]);
  });

  test('keeps a later citation on its own marker when an earlier one was dropped', () => {
    const result = toChatCitations('Texto [1] y [2].', [cite({ n: 2, orden: 2 })]);
    expect(result[0].n).toBe(2);
    expect(result[0].orden).toBe(2);
  });

  test('falls back to the positional guess when n and orden are missing', () => {
    const answer = 'Texto [5], luego [2], otra vez [5].';
    const result = toChatCitations(answer, [cite(), cite({ n: null, orden: null })]);
    expect(result.map((c) => [c.n, c.orden])).toEqual([
      [5, 1],
      [2, 2],
    ]);
  });
});
