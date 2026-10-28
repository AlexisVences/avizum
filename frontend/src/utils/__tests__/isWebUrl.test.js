import isWebUrl from '../isWebUrl';

test('accepts http and https only', () => {
  expect(isWebUrl('https://x.mx/r.pdf#page=3')).toBe(true);
  expect(isWebUrl('http://x.mx')).toBe(true);
  expect(isWebUrl('javascript:alert(1)')).toBe(false);
  expect(isWebUrl('data:text/html,hi')).toBe(false);
  expect(isWebUrl('/relativo')).toBe(false);
  expect(isWebUrl('')).toBe(false);
  expect(isWebUrl(null)).toBe(false);
});
