import {
    getCategoriasPublicadas,
    getCategoriaPorSlug,
    getArticulosPorCategoria,
    getArticuloPorSlug,
    getHerramientas,
    getHerramientaPorSlug,
    buscarEnGuia,
} from '../guiaService';

const categoriasFixture = [
    { id: '01', numero: '01', etiqueta: 'LEYES', titulo: 'Marco jurídico', bloque: 'Leyes y derechos', slug: 'marco-juridico', orden: 1, published: true },
    { id: '02', numero: '02', etiqueta: 'DERECHOS', titulo: 'Si te detiene un agente', bloque: 'Leyes y derechos', slug: 'si-te-detiene-un-agente', orden: 2, published: false },
];

const articulosFixture = [
    {
        titulo: 'Marco jurídico', categoria: 'marco-juridico', slug: 'marco-juridico',
        resumen: 'Los cinco documentos oficiales.', tipo: 'documentos', documentos: [], fuentes: [],
        actualizado: '2026-10', keywords: ['reglamento', 'ley de movilidad'], published: true,
    },
    {
        titulo: 'Artículo sin publicar', categoria: 'marco-juridico', slug: 'borrador',
        resumen: 'Todavía no.', tipo: 'prosa', cuerpo: '...', fuentes: [],
        actualizado: '2026-10', keywords: [], published: false,
    },
];

const herramientasFixture = [
    { id: 'uma-a-pesos', slug: 'uma-a-pesos', titulo: 'UMA → pesos', descripcion: '...', published: false },
];

describe('getCategoriasPublicadas', () => {
    it('returns only published categories sorted by orden', () => {
        const resultado = getCategoriasPublicadas(categoriasFixture);
        expect(resultado).toHaveLength(1);
        expect(resultado[0].slug).toBe('marco-juridico');
    });
});

describe('getCategoriaPorSlug', () => {
    it('finds a category by slug regardless of published status', () => {
        expect(getCategoriaPorSlug('si-te-detiene-un-agente', categoriasFixture)?.titulo).toBe('Si te detiene un agente');
    });

    it('returns null for an unknown slug', () => {
        expect(getCategoriaPorSlug('no-existe', categoriasFixture)).toBeNull();
    });
});

describe('getArticulosPorCategoria', () => {
    it('returns only published articles for the category', () => {
        const resultado = getArticulosPorCategoria('marco-juridico', articulosFixture);
        expect(resultado).toHaveLength(1);
        expect(resultado[0].slug).toBe('marco-juridico');
    });
});

describe('getArticuloPorSlug', () => {
    it('returns the published article matching category and slug', () => {
        const articulo = getArticuloPorSlug('marco-juridico', 'marco-juridico', articulosFixture);
        expect(articulo?.titulo).toBe('Marco jurídico');
    });

    it('returns null for an unpublished article (treated as not found)', () => {
        expect(getArticuloPorSlug('marco-juridico', 'borrador', articulosFixture)).toBeNull();
    });

    it('returns null when the category does not match', () => {
        expect(getArticuloPorSlug('otra-categoria', 'marco-juridico', articulosFixture)).toBeNull();
    });
});

describe('getHerramientas', () => {
    it('returns only published tools', () => {
        expect(getHerramientas(herramientasFixture)).toHaveLength(0);
    });
});

describe('getHerramientaPorSlug', () => {
    it('finds a tool by slug even when unpublished', () => {
        expect(getHerramientaPorSlug('uma-a-pesos', herramientasFixture)?.titulo).toBe('UMA → pesos');
    });

    it('returns null for an unknown tool slug', () => {
        expect(getHerramientaPorSlug('no-existe', herramientasFixture)).toBeNull();
    });
});

describe('buscarEnGuia', () => {
    it('returns all published categories when the query is empty', () => {
        expect(buscarEnGuia('', categoriasFixture, articulosFixture)).toHaveLength(1);
    });

    it('matches by category title, case and accent insensitive', () => {
        expect(buscarEnGuia('JURIDICO', categoriasFixture, articulosFixture)).toHaveLength(1);
    });

    it('matches a category through one of its article keywords', () => {
        expect(buscarEnGuia('reglamento', categoriasFixture, articulosFixture)).toHaveLength(1);
    });

    it('returns an empty list when nothing matches', () => {
        expect(buscarEnGuia('xyz-no-existe', categoriasFixture, articulosFixture)).toHaveLength(0);
    });

    it('never returns an unpublished category even if its title matches', () => {
        expect(buscarEnGuia('detiene', categoriasFixture, articulosFixture)).toHaveLength(0);
    });
});
