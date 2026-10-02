export function obtenerPeriodoVerificacion(ultimoDigito, calendario) {
    if (!Array.isArray(calendario) || calendario.length === 0) {
        return null;
    }
    const digito = Number(ultimoDigito);
    if (Number.isNaN(digito) || digito < 0 || digito > 9) {
        return null;
    }
    return calendario.find((entrada) => entrada.digitos.includes(digito)) || null;
}
