export function convertirUmaAPesos(cantidadUma, valorDiario) {
    if (valorDiario === null || valorDiario === undefined) {
        return null;
    }
    const cantidad = Number(cantidadUma);
    if (Number.isNaN(cantidad)) {
        return null;
    }
    return cantidad * Number(valorDiario);
}
