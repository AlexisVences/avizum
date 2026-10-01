import React, { useEffect, useState, useRef } from "react";
import { useLocation } from "react-router-dom";
import NavBar2 from "../components/NavBar2";
import { FaPaperPlane, FaStar, FaBars, FaTimes } from "react-icons/fa";
import { consultarChatLegal, enviarFeedbackLegal } from "../services/legalService";
import authService from "../services/authService";

const AsesoriaIA = () => {
    const location = useLocation();
    const storedUser = authService.getCurrentUser();
    const userId = storedUser?.id;
    const chatHistoryRef = useRef(null);
    const messageRefs = useRef([]);

    useEffect(() => {
        window.scrollTo(0, 0);
    }, [location]);

    const [consulta, setConsulta] = useState("");
    const [historial, setHistorial] = useState([]);
    const [hoveredRating, setHoveredRating] = useState({});
    const [selectedRatings, setSelectedRatings] = useState({});
    const [menuAbierto, setMenuAbierto] = useState(false);

    useEffect(() => {
        // Baja solo el contenedor del chat, no la ventana -- scrollIntoView
        // arrastraría también el scroll de la página completa.
        if (historial.length > 0 && chatHistoryRef.current) {
            chatHistoryRef.current.scrollTo({ top: chatHistoryRef.current.scrollHeight, behavior: "smooth" });
        }
    }, [historial]);

    const manejarEnvio = async () => {
        if (consulta.trim() === "") return;

        const nuevaEntrada = {
            pregunta: consulta,
            respuesta: "Cargando...",
        };

        setHistorial((prev) => [...prev, nuevaEntrada]); // Coloca la nueva consulta al final
        setConsulta("");

        try {
            const data = await consultarChatLegal(consulta, userId);
            const nuevaRespuesta = {
                pregunta: consulta,
                respuesta: data.respuesta,
                fuentes: data.fuentes,
                categoria: data.categoria,
                id_respuesta: data.id_respuesta, //guardar por cada respuesta
            };
            setHistorial((prev) => {
                const actualizado = [...prev];
                actualizado[actualizado.length - 1] = nuevaRespuesta;
                return actualizado;
            });
        } catch (error) {
            const errorRespuesta = {
                pregunta: consulta,
                respuesta: "Ocurrió un error al procesar tu consulta. Intenta nuevamente.",
            };
            setHistorial((prev) => {
                const actualizado = [...prev];
                actualizado[actualizado.length - 1] = errorRespuesta;
                return actualizado;
            });
        }
    };

    // envia calificacion al backend
    const calificarRespuesta = async (index, rating) => {
        const item = historial[index];
        setSelectedRatings((prev) => ({ ...prev, [index]: rating }));

        try {
            await enviarFeedbackLegal({
                userId,
                pregunta: item.pregunta,
                respuesta: item.id_respuesta,
                rating,
            });
        } catch (error) {
            console.error("Error al enviar calificación:", error);
        }
    };

    const irAPregunta = (index) => {
        setMenuAbierto(false);
        messageRefs.current[index]?.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const hayConversacion = historial.length > 0;

    return (
        <>
            <NavBar2 />
            <div className="tw-pt-16 tw-h-screen tw-flex tw-flex-col tw-bg-paper tw-overflow-hidden">
                {/* Header interno del chat -- distinto del Navbar del sitio */}
                <div className="tw-shrink-0 tw-flex tw-items-center tw-gap-3 tw-px-4 sm:tw-px-6 tw-py-3 tw-border-b tw-border-rule">
                    <button
                        type="button"
                        aria-label={menuAbierto ? "Cerrar historial" : "Abrir historial"}
                        onClick={() => setMenuAbierto((v) => !v)}
                        className="tw-w-9 tw-h-9 tw-flex tw-items-center tw-justify-center tw-rounded tw-border tw-border-ink/15 tw-text-ink hover:tw-border-ink/40 tw-transition-colors"
                    >
                        <FaBars size={14} />
                    </button>
                    <span className="tw-font-display tw-font-semibold tw-text-ink">Asesoría legal</span>
                </div>

                <div className="tw-relative tw-flex-1 tw-min-h-0 tw-flex">
                    {/* Drawer de historial */}
                    {menuAbierto && (
                        <button
                            aria-label="Cerrar historial"
                            onClick={() => setMenuAbierto(false)}
                            className="tw-fixed tw-inset-0 tw-top-[calc(4rem+49px)] tw-bg-ink/30 tw-z-40 tw-border-0 tw-cursor-default"
                        />
                    )}
                    <aside
                        inert={!menuAbierto}
                        className={`tw-fixed tw-top-[calc(4rem+49px)] tw-bottom-0 tw-left-0 tw-w-72 tw-max-w-[80vw] tw-bg-paper-raised tw-border-r tw-border-rule tw-z-50 tw-flex tw-flex-col tw-transition-transform tw-duration-200 ${menuAbierto ? "tw-translate-x-0" : "-tw-translate-x-full"}`}
                    >
                        <div className="tw-flex tw-items-center tw-justify-between tw-px-4 tw-py-3 tw-border-b tw-border-rule">
                            <h2 className="tw-font-display tw-text-base tw-font-semibold tw-text-ink tw-m-0">
                                Historial de consultas
                            </h2>
                            <button
                                aria-label="Cerrar historial"
                                onClick={() => setMenuAbierto(false)}
                                className="tw-w-7 tw-h-7 tw-flex tw-items-center tw-justify-center tw-rounded tw-text-ink-soft hover:tw-text-ink"
                            >
                                <FaTimes size={13} />
                            </button>
                        </div>
                        <div className="tw-flex-1 tw-overflow-y-auto tw-p-3">
                            {!hayConversacion ? (
                                <p className="tw-text-ink-soft tw-text-sm tw-px-1">Tu historial aparecerá aquí.</p>
                            ) : (
                                <ul className="tw-list-none tw-p-0 tw-m-0 tw-flex tw-flex-col tw-gap-1">
                                    {historial.map((item, index) => (
                                        <li key={index}>
                                            <button
                                                onClick={() => irAPregunta(index)}
                                                className="tw-w-full tw-text-left tw-text-sm tw-text-ink-soft hover:tw-bg-gris tw-rounded tw-px-2.5 tw-py-2 tw-transition-colors"
                                            >
                                                {item.pregunta.slice(0, 60)}{item.pregunta.length > 60 ? '…' : ''}
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    </aside>

                    {/* Columna de chat */}
                    <div className="tw-flex-1 tw-min-w-0 tw-flex tw-flex-col">
                        {!hayConversacion ? (
                            <div className="tw-flex-1 tw-flex tw-flex-col tw-items-center tw-justify-center tw-px-4">
                                <h1 className="tw-font-display tw-text-2xl sm:tw-text-3xl tw-font-semibold tw-text-ink tw-mb-2 tw-text-center">
                                    ¿En qué te puedo ayudar?
                                </h1>
                                <p className="tw-text-ink-soft tw-text-sm tw-mb-6 tw-text-center tw-max-w-md">
                                    Respuestas basadas solo en el Reglamento de Tránsito y la Ley de
                                    Movilidad de la CDMX — nunca inventadas.
                                </p>
                                <div className="tw-w-full tw-max-w-xl tw-flex tw-gap-2 tw-bg-paper-raised tw-border tw-border-rule tw-rounded-full tw-shadow-sm tw-px-2 tw-py-2">
                                    <input
                                        type="text"
                                        placeholder="Escribe tu consulta legal aquí…"
                                        value={consulta}
                                        onChange={(e) => setConsulta(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && manejarEnvio()}
                                        className="tw-flex-1 tw-min-w-0 tw-bg-transparent tw-border-0 tw-px-3 tw-text-ink placeholder:tw-text-ink-soft/60 focus:tw-outline-none"
                                    />
                                    <button
                                        onClick={manejarEnvio}
                                        aria-label="Enviar"
                                        className="tw-w-10 tw-h-10 tw-shrink-0 tw-flex tw-items-center tw-justify-center tw-rounded-full tw-bg-ink tw-text-white hover:tw-bg-magenta tw-transition-colors"
                                    >
                                        <FaPaperPlane size={14} />
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                <div ref={chatHistoryRef} className="tw-flex-1 tw-overflow-y-auto tw-px-4 sm:tw-px-6 tw-py-6">
                                    <div className="tw-max-w-2xl tw-mx-auto tw-flex tw-flex-col tw-gap-8">
                                        {historial.map((item, index) => (
                                            <div key={index} ref={(el) => (messageRefs.current[index] = el)}>
                                                <div className="tw-flex tw-justify-end tw-mb-4">
                                                    <div className="tw-max-w-[80%] tw-bg-ink tw-text-white tw-rounded-lg tw-rounded-tr-sm tw-px-4 tw-py-2.5 tw-text-sm">
                                                        {item.pregunta}
                                                    </div>
                                                </div>

                                                <div>
                                                    <div className="tw-font-mono tw-text-[10px] tw-font-bold tw-tracking-wide tw-text-ink-soft tw-uppercase tw-mb-1.5">
                                                        Amicuz IA
                                                    </div>

                                                    {item.respuesta === "Cargando..." ? (
                                                        <div className="tw-flex tw-gap-1 tw-py-1">
                                                            <span className="tw-w-1.5 tw-h-1.5 tw-rounded-full tw-bg-ink-soft/50 tw-animate-bounce [animation-delay:-0.3s]"></span>
                                                            <span className="tw-w-1.5 tw-h-1.5 tw-rounded-full tw-bg-ink-soft/50 tw-animate-bounce [animation-delay:-0.15s]"></span>
                                                            <span className="tw-w-1.5 tw-h-1.5 tw-rounded-full tw-bg-ink-soft/50 tw-animate-bounce"></span>
                                                        </div>
                                                    ) : (
                                                        <div className="tw-text-ink tw-text-[0.95rem] tw-leading-relaxed">
                                                            {item.respuesta.split('\n').map((linea, i) => (
                                                                <React.Fragment key={i}>
                                                                    {linea}
                                                                    <br />
                                                                </React.Fragment>
                                                            ))}
                                                        </div>
                                                    )}

                                                    {(item.categoria || (item.fuentes && item.fuentes.length > 0)) && (
                                                        <div className="tw-mt-2.5 tw-flex tw-flex-wrap tw-items-center tw-gap-2">
                                                            {item.categoria && (
                                                                <span className="tw-font-mono tw-text-[10px] tw-font-bold tw-tracking-wide tw-text-magenta tw-uppercase">
                                                                    {item.categoria}
                                                                </span>
                                                            )}
                                                            {item.fuentes && item.fuentes.map((fuente, fi) => (
                                                                <span
                                                                    key={fi}
                                                                    className="tw-font-mono tw-text-[10px] tw-text-ink-soft tw-bg-gris tw-border tw-border-rule tw-rounded tw-px-1.5 tw-py-0.5"
                                                                >
                                                                    {fuente.document}{fuente.page ? ` · p.${fuente.page}` : ''}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}

                                                    {item.id_respuesta && (
                                                        <div className="tw-flex tw-items-center tw-gap-1 tw-mt-2.5">
                                                            {[1, 2, 3, 4, 5].map((estrella) => (
                                                                <FaStar
                                                                    key={estrella}
                                                                    size={14}
                                                                    className="tw-cursor-pointer"
                                                                    color={
                                                                        (hoveredRating[index] || selectedRatings[index]) >= estrella
                                                                            ? "#F5A524"
                                                                            : "#DDD8CC"
                                                                    }
                                                                    onMouseEnter={() => setHoveredRating((prev) => ({ ...prev, [index]: estrella }))}
                                                                    onMouseLeave={() => setHoveredRating((prev) => ({ ...prev, [index]: null }))}
                                                                    onClick={() => calificarRespuesta(index, estrella)}
                                                                />
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="tw-shrink-0 tw-border-t tw-border-rule tw-px-4 sm:tw-px-6 tw-py-4">
                                    <div className="tw-max-w-2xl tw-mx-auto tw-flex tw-gap-2 tw-bg-paper-raised tw-border tw-border-rule tw-rounded-full tw-shadow-sm tw-px-2 tw-py-2">
                                        <input
                                            type="text"
                                            placeholder="Escribe tu consulta legal aquí…"
                                            value={consulta}
                                            onChange={(e) => setConsulta(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && manejarEnvio()}
                                            className="tw-flex-1 tw-min-w-0 tw-bg-transparent tw-border-0 tw-px-3 tw-text-ink placeholder:tw-text-ink-soft/60 focus:tw-outline-none"
                                        />
                                        <button
                                            onClick={manejarEnvio}
                                            aria-label="Enviar"
                                            className="tw-w-10 tw-h-10 tw-shrink-0 tw-flex tw-items-center tw-justify-center tw-rounded-full tw-bg-ink tw-text-white hover:tw-bg-magenta tw-transition-colors"
                                        >
                                            <FaPaperPlane size={14} />
                                        </button>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
};

export default AsesoriaIA;
