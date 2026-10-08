import React from 'react';
import { useParams, Link } from 'react-router-dom';
import NavBar2 from '../components/NavBar2';
import Footer from '../components/Footer';
import { getArticuloPorSlug, getCategoriaPorSlug } from '../services/guiaService';
import ArticuloContenido from '../components/guia/ArticuloContenido';

const GuiaArticulo = () => {
    const { categoriaSlug, articuloSlug } = useParams();
    const categoria = getCategoriaPorSlug(categoriaSlug);
    const articulo = getArticuloPorSlug(categoriaSlug, articuloSlug);

    if (!categoria || !articulo) {
        return (
            <>
                <NavBar2 />
                <main className="tw-pt-16">
                    <div className="tw-max-w-[680px] tw-mx-auto tw-px-6 tw-py-16 tw-text-center">
                        <p className="tw-font-mono tw-text-[11px] tw-uppercase tw-tracking-widest tw-text-magenta tw-font-bold tw-mb-3">
                            404
                        </p>
                        <h1 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-mb-3">
                            No encontramos este artículo
                        </h1>
                        <p className="tw-text-ink-soft tw-mb-6">
                            Puede que el contenido todavía no esté publicado o que la dirección sea incorrecta.
                        </p>
                        <Link to="/Bienvenida" className="tw-text-azul hover:tw-text-magenta tw-font-semibold">
                            ← Volver a Bienvenida
                        </Link>
                    </div>
                </main>
                <Footer />
            </>
        );
    }

    return (
        <>
            <NavBar2 />
            <main className="tw-pt-16">
                <ArticuloContenido categoria={categoria} articulo={articulo} />
            </main>
            <Footer />
        </>
    );
};

export default GuiaArticulo;
