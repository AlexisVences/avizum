import { convertirUmaAPesos } from '../umaCalculator';

describe('convertirUmaAPesos', () => {
    it('multiplies the UMA quantity by the daily value', () => {
        expect(convertirUmaAPesos(10, 108.57)).toBeCloseTo(1085.7);
    });

    it('returns null when the official daily value is not loaded yet', () => {
        expect(convertirUmaAPesos(10, null)).toBeNull();
    });

    it('returns null for a non-numeric quantity', () => {
        expect(convertirUmaAPesos('abc', 108.57)).toBeNull();
    });

    it('returns 0 for a zero quantity', () => {
        expect(convertirUmaAPesos(0, 108.57)).toBe(0);
    });

    it('returns null for an empty quantity (nothing typed yet)', () => {
        expect(convertirUmaAPesos('', 108.57)).toBeNull();
    });

    it('returns null for a negative quantity', () => {
        expect(convertirUmaAPesos(-5, 108.57)).toBeNull();
    });
});
