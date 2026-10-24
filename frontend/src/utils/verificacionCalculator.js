// En la CDMX se verifica dos veces al año (un periodo por semestre) y cada
// periodo dura dos meses. El calendario lista, por último dígito de placa, el
// color del engomado y sus dos periodos: el del primer y el del segundo semestre.
export function obtenerPeriodoVerificacion(ultimoDigito, calendario) {
    if (!Array.isArray(calendario) || calendario.length === 0) {
        return null;
    }
    if (ultimoDigito === '' || ultimoDigito === null || ultimoDigito === undefined) {
        return null;
    }
    const digito = Number(ultimoDigito);
    if (!Number.isInteger(digito) || digito < 0 || digito > 9) {
        return null;
    }
    return calendario.find((entrada) => entrada.digitos.includes(digito)) || null;
}
