import { useCallback, useEffect, useRef, useState } from 'react';

const DEFAULT_ERROR = 'No pudimos cargar la información. Intenta de nuevo.';

// Pide `fetcher(params)` al montar y cada vez que cambian los parámetros; descarta respuestas viejas.
const useAdminList = (fetcher, params) => {
    const [state, setState] = useState({ data: null, loading: true, error: null });
    const [version, setVersion] = useState(0);
    const latest = useRef(0);
    const fetcherRef = useRef(fetcher);
    fetcherRef.current = fetcher;
    const key = JSON.stringify(params);

    useEffect(() => {
        const id = ++latest.current;
        setState((prev) => ({ ...prev, loading: true, error: null }));
        fetcherRef
            .current(JSON.parse(key))
            .then((data) => {
                if (id === latest.current) setState({ data, loading: false, error: null });
            })
            .catch((err) => {
                if (id === latest.current) {
                    setState({ data: null, loading: false, error: err?.message || DEFAULT_ERROR });
                }
            });
        return () => {
            // Invalida la petición en curso si cambian los parámetros o se desmonta.
            latest.current += 1;
        };
    }, [key, version]);

    const reload = useCallback(() => setVersion((v) => v + 1), []);
    return { ...state, reload };
};

export default useAdminList;
