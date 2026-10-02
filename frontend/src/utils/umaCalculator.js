export function convertirUmaAPesos(cantidadUma, valorDiario) {
    if (valorDiario === null || valorDiario === undefined) {
        return null;
    }
    if (cantidadUma === '' || cantidadUma === null || cantidadUma === undefined) {
        return null;
    }
    const cantidad = Number(cantidadUma);
    if (Number.isNaN(cantidad) || cantidad < 0) {
        return null;
    }
    return cantidad * Number(valorDiario);
}
