import React, { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AuthCard, { ErrorBox, StatusBox, linkClass } from "../components/AuthCard";
import Button from "../components/ui/Button";
import { verifyEmail, resendVerification } from "../services/emailAccountService";

const VerificarCorreo = () => {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [estado, setEstado] = useState(token ? "cargando" : "error");
  const [error, setError] = useState(token ? "" : "El enlace no es válido: falta el código de verificación.");
  const [reenvio, setReenvio] = useState({ enviando: false, ok: false, error: "" });
  const lanzado = useRef(false);
  const sesionActiva = !!localStorage.getItem("token");

  useEffect(() => {
    if (!token || lanzado.current) return;
    lanzado.current = true;
    verifyEmail(token)
      .then(() => {
        try {
          const user = JSON.parse(localStorage.getItem("user"));
          if (user) localStorage.setItem("user", JSON.stringify({ ...user, emailVerificado: true }));
        } catch (e) {
          /* stored session unreadable: nothing to update */
        }
        setEstado("ok");
      })
      .catch((err) => {
        setError(err.message);
        setEstado("error");
      });
  }, [token]);

  const reenviar = async () => {
    setReenvio({ enviando: true, ok: false, error: "" });
    try {
      await resendVerification();
      setReenvio({ enviando: false, ok: true, error: "" });
    } catch (err) {
      setReenvio({ enviando: false, ok: false, error: err.message });
    }
  };

  return (
    <AuthCard title="Verificación de correo" focusKey={estado}>
      {estado === "cargando" && (
        <p role="status" className="tw-text-ink-soft tw-m-0">Verificando tu correo...</p>
      )}

      {estado === "ok" && (
        <>
          <StatusBox>Tu correo quedó verificado.</StatusBox>
          <Button to={sesionActiva ? "/Bienvenida" : "/Login"} variant="dark" size="lg" className="tw-w-full">
            {sesionActiva ? "Ir a la aplicación" : "Iniciar sesión"}
          </Button>
        </>
      )}

      {estado === "error" && (
        <>
          <ErrorBox>{error}</ErrorBox>
          {reenvio.error && <ErrorBox>{reenvio.error}</ErrorBox>}
          {reenvio.ok && <StatusBox>Te enviamos un nuevo enlace. Revisa tu correo.</StatusBox>}
          {sesionActiva ? (
            <Button variant="dark" size="lg" className="tw-w-full" onClick={reenviar} disabled={reenvio.enviando || reenvio.ok}>
              {reenvio.enviando ? "Enviando..." : "Solicitar un nuevo enlace"}
            </Button>
          ) : (
            <p className="tw-text-sm tw-text-ink-soft tw-m-0">
              Inicia sesión para solicitar un nuevo enlace.{" "}
              <Link to="/Login" className={linkClass}>Iniciar sesión</Link>
            </p>
          )}
        </>
      )}
    </AuthCard>
  );
};

export default VerificarCorreo;
