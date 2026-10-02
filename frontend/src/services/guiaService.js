import categoriasData from '../content/guia/categorias.json';
import herramientasData from '../content/guia/herramientas.json';
import { cargarArticulos } from '../content/guia/loadArticulos';

const normalizar = (texto) =>
    (texto || '')
        .toString()
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .toLowerCase();

export function getCategoriasPublicadas(categorias = categoriasData) {
    return categorias
        .filter((categoria) => categoria.published)
        .slice()
        .sort((a, b) => a.orden - b.orden);
}

export function getCategoriaPorSlug(slug, categorias = categoriasData) {
    return categorias.find((categoria) => categoria.slug === slug) || null;
}

export function getArticulosPorCategoria(categoriaSlug, articulos = cargarArticulos()) {
    return articulos
        .filter((articulo) => articulo.categoria === categoriaSlug && articulo.published)
        .slice()
        .sort((a, b) => a.titulo.localeCompare(b.titulo));
}

export function getArticuloPorSlug(categoriaSlug, articuloSlug, articulos = cargarArticulos()) {
    return (
        articulos.find(
            (articulo) =>
                articulo.categoria === categoriaSlug &&
                articulo.slug === articuloSlug &&
                articulo.published
        ) || null
    );
}

export function getHerramientas(herramientas = herramientasData) {
    return herramientas.filter((herramienta) => herramienta.published);
}

export function getHerramientaPorSlug(slug, herramientas = herramientasData) {
    // Unlike articles, a tool is safe to reach directly even while unpublished:
    // the UI always falls back to a "sin datos oficiales todavía" state (see
    // UmaCalculadora/VerificacionCalculadora in Task 6) — it never shows a
    // fabricated number, so there's no fabrication risk in exposing the route.
    return herramientas.find((herramienta) => herramienta.slug === slug) || null;
}

export function buscarEnGuia(query, categorias = categoriasData, articulos = cargarArticulos()) {
    const normalizada = normalizar(query);
    const categoriasPublicadas = getCategoriasPublicadas(categorias);

    if (!normalizada) {
        return categoriasPublicadas;
    }

    return categoriasPublicadas.filter((categoria) => {
        const coincideCategoria = [categoria.titulo, categoria.etiqueta].some((campo) =>
            normalizar(campo).includes(normalizada)
        );
        if (coincideCategoria) return true;

        return getArticulosPorCategoria(categoria.slug, articulos).some((articulo) =>
            [articulo.titulo, articulo.resumen, ...(articulo.keywords || [])].some((campo) =>
                normalizar(campo).includes(normalizada)
            )
        );
    });
}
