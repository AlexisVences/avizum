import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import logo from '../../assets/logo.png';

// The logo sits behind the hero as a huge, heavily blurred shape — a mood, not
// a mark. The mask lives on the wrapper (not the image) so the fade ends
// exactly at the hero's bottom edge instead of being cut off by it.
const MASCARA_FONDO = 'linear-gradient(to bottom, #000 30%, transparent 100%)';

const HeroBienvenida = ({ nombre }) => {
    const reducirMovimiento = useReducedMotion();
    const saludo = typeof nombre === 'string' ? nombre.trim() : '';

    const entrada = (retraso) =>
        reducirMovimiento
            ? {}
            : {
                  initial: { opacity: 0, y: 18 },
                  animate: { opacity: 1, y: 0 },
                  transition: { duration: 0.7, delay: retraso, ease: [0.2, 0.7, 0.2, 1] },
              };

    return (
        <section className="tw-relative tw-overflow-hidden tw-bg-paper tw-px-6 tw-pt-24 tw-pb-14">
            <div
                aria-hidden="true"
                className="tw-pointer-events-none tw-absolute tw-inset-0 tw-overflow-hidden"
                style={{ WebkitMaskImage: MASCARA_FONDO, maskImage: MASCARA_FONDO }}
            >
                <img
                    src={logo}
                    alt=""
                    aria-hidden="true"
                    className="tw-select-none tw-absolute -tw-right-24 -tw-top-10 tw-w-[min(900px,95vw)] tw-max-w-none tw-blur-[48px] tw-opacity-[0.08] tw-animate-deriva motion-reduce:tw-animate-none"
                />
            </div>

            <div className="tw-relative tw-mx-auto tw-max-w-5xl">
                {saludo && (
                    <motion.p
                        {...entrada(0)}
                        className="tw-font-mono tw-text-[12px] tw-font-bold tw-uppercase tw-tracking-widest tw-text-magenta tw-mb-4"
                    >
                        {`Hola, ${saludo}.`}
                    </motion.p>
                )}
                <motion.h1
                    {...entrada(0.1)}
                    className="tw-font-display tw-font-semibold tw-text-[clamp(2.2rem,5vw,3.6rem)] tw-leading-[1.05] tw-text-ink tw-mb-4 [text-wrap:balance]"
                >
                    Bienvenido a <span className="tw-text-magenta">Amicuz</span>
                </motion.h1>
                <motion.p
                    {...entrada(0.2)}
                    className="tw-text-[1.1rem] tw-text-ink-soft tw-max-w-[52ch] tw-mb-10"
                >
                    Tu plataforma de confianza para resolver cualquier situación legal de tránsito.
                </motion.p>
                <motion.div {...entrada(0.3)}>
                    <h2 className="tw-font-display tw-font-semibold tw-text-2xl tw-text-ink tw-mb-1.5">
                        ¿Cómo podemos ayudarte?
                    </h2>
                    <p className="tw-text-ink-soft tw-m-0">
                        Elige la opción que mejor se acomode a tus necesidades
                    </p>
                </motion.div>
            </div>
        </section>
    );
};

export default HeroBienvenida;
