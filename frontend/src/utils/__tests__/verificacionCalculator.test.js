import { obtenerPeriodoVerificacion } from '../verificacionCalculator';

const calendarioFixture = [
    { digitos: [0, 1], periodo: 'Noviembre-Diciembre', color: 'Verde' },
    { digitos: [5, 6], periodo: 'Enero-Febrero', color: 'Amarillo' },
    { digitos: [7, 8], periodo: 'Marzo-Abril', color: 'Rosa' },
];

describe('obtenerPeriodoVerificacion', () => {
    it('finds the period matching the last digit', () => {
        expect(obtenerPeriodoVerificacion(5, calendarioFixture)).toEqual(calendarioFixture[1]);
    });

    it('finds the period for an explicit digit 0 (distinct from empty input)', () => {
        expect(obtenerPeriodoVerificacion(0, calendarioFixture)).toEqual(calendarioFixture[0]);
    });

    it('returns null when the calendar has not been loaded yet', () => {
        expect(obtenerPeriodoVerificacion(5, [])).toBeNull();
    });

    it('returns null for a digit outside 0-9', () => {
        expect(obtenerPeriodoVerificacion(15, calendarioFixture)).toBeNull();
    });

    it('returns null for a non-numeric digit', () => {
        expect(obtenerPeriodoVerificacion('x', calendarioFixture)).toBeNull();
    });

    it('returns null for an empty digit (nothing typed yet)', () => {
        expect(obtenerPeriodoVerificacion('', calendarioFixture)).toBeNull();
    });

    it('returns null for a non-integer digit', () => {
        expect(obtenerPeriodoVerificacion(5.5, calendarioFixture)).toBeNull();
    });
});
