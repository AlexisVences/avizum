// require.context is a webpack-only API — Jest can't execute it. Keeping the
// call inside the function body (not at module top level) means merely
// importing this module is safe under Jest; only an actual call to
// cargarArticulos() touches require.context. guiaService.js uses this as a
// default-parameter expression, which JS only evaluates when the caller
// omits the argument — tests always pass fixtures explicitly, so they never
// reach this line.
let cache = null;

export function cargarArticulos() {
    if (cache === null) {
        const articuloModules = require.context('./articulos', false, /\.json$/);
        cache = articuloModules.keys().map((key) => articuloModules(key));
    }
    return cache;
}
