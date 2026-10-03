import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

// Fades/slides its children in once they scroll into view. Renders a plain
// wrapper when the user prefers reduced motion.
const Revelar = ({ retraso = 0, className = '', children }) => {
    const reducirMovimiento = useReducedMotion();

    if (reducirMovimiento) {
        return <div className={className}>{children}</div>;
    }

    return (
        <motion.div
            className={className}
            initial={{ opacity: 0, y: 28 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-40px' }}
            transition={{ duration: 0.6, delay: retraso, ease: [0.2, 0.7, 0.2, 1] }}
        >
            {children}
        </motion.div>
    );
};

export default Revelar;
