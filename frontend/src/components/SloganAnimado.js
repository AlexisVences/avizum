import React from "react";
import "../styles/SloganAnimado.css";

const SloganAnimado = () => {
    return (
        <p className="slogan-animado" aria-label="Verifica. Entiende. Decide.">
            <span className="slogan-animado__word slogan-animado__word--1">Verifica</span>
            <span className="slogan-animado__dot" aria-hidden="true">·</span>
            <span className="slogan-animado__word slogan-animado__word--2">Asesorate</span>
            <span className="slogan-animado__dot slogan-animado__dot--2" aria-hidden="true">·</span>
            <span className="slogan-animado__word slogan-animado__word--3">Conduce</span>
        </p>
    );
};

export default SloganAnimado;
