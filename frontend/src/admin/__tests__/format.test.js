import { formatDate, fullName } from '../format';

test('formatDate uses the Mexico City calendar day', () => {
  // 03:00 UTC on the 21st is still the evening of the 20th in Mexico City (UTC-6).
  expect(formatDate('2026-10-21T03:00:00Z')).toBe('20 oct 2026');
  expect(formatDate(null)).toBeNull();
});

test('fullName joins the parts that exist', () => {
  expect(fullName('Ana', 'Ruiz')).toBe('Ana Ruiz');
  expect(fullName('Ana', '')).toBe('Ana');
  expect(fullName(undefined, undefined)).toBe('');
});
