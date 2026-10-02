import React from 'react';
import { useParams, Link } from 'react-router-dom';
import NavBar2 from '../components/NavBar2';
import Footer from '../components/Footer';
import { getCategoriaPorSlug, getArticulosPorCategoria, getHerramientas } from '../services/guiaService';

const GuiaCategoria = () => {
    const { categoriaSlug } = useParams();
    const categoria = getCategoriaPorSlug(categoriaSlug);

    if (!categoria || !categoria.published) {
        return (
            <>
                <NavBar2 />
                <main className="tw-pt-16">
                    <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-16 tw-text-center">
                        <p className="tw-font-mono tw-text-[11px] tw-uppercase tw-tracking-widest tw-text-magenta tw-font-bold tw-mb-3">404</p>
                        <h1 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-mb-3">
                            No encontramos esta categoría
                        </h1>
                        <Link to="/Bienvenida" className="tw-text-azul hover:tw-text-magenta tw-font-semibold">
                            ← Volver a Bienvenida
                        </Link>
                    </div>
                </main>
                <Footer />
            </>
        );
    }

    const esCalculadoras = categoria.slug === 'calculadoras';
    const items = esCalculadoras ? getHerramientas() : getArticulosPorCategoria(categoriaSlug);

    return (
        <>
            <NavBar2 />
            <main className="tw-pt-16">
                <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-12">
                    <span className="tw-block tw-font-mono tw-text-[11px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-3">
                        {categoria.numero} · {categoria.etiqueta}
                    </span>
                    <h1 className="tw-font-display tw-text-3xl tw-font-semibold tw-text-ink tw-mb-8">
                        {categoria.titulo}
                    </h1>

                    {items.length === 0 && (
                        <p className="tw-text-ink-soft tw-text-sm">
                            Aún no hay contenido publicado en esta categoría.
                        </p>
                    )}

                    <ul className="tw-list-none tw-p-0 tw-m-0 tw-flex tw-flex-col tw-gap-3">
                        {items.map((item) => (
                            <li key={item.slug}>
                                <Link
                                    to={esCalculadoras ? `/guia/calculadoras/${item.slug}` : `/guia/${categoriaSlug}/${item.slug}`}
                                    className="tw-block tw-border tw-border-rule tw-rounded tw-px-4 tw-py-3.5 tw-no-underline tw-text-inherit hover:tw-bg-paper tw-transition-colors"
                                >
                                    <span className="tw-block tw-text-ink tw-font-semibold tw-text-sm">
                                        {item.titulo}
                                    </span>
                                    {(item.resumen || item.descripcion) && (
                                        <span className="tw-block tw-text-ink-soft tw-text-sm tw-mt-1">
                                            {item.resumen || item.descripcion}
                                        </span>
                                    )}
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>
            </main>
            <Footer />
        </>
    );
};

export default GuiaCategoria;
