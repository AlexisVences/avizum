import React, { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AuthCard, { ErrorBox, StatusBox, linkClass } from "../components/AuthCard";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { resetPassword } from "../services/emailAccountService";

const RestablecerContrasena = () => {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [password, setPassword] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [listo, setListo] = useState(false);
  const [error, setError] = useState("");
  const [tokenInvalido, setTokenInvalido] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (password !== confirmacion) {
      setError("Las contraseñas no coinciden");
      return;
    }
    setEnviando(true);
    try {
      await resetPassword(token, password);
      setListo(true);
    } catch (err) {
      // 400 = bad/expired/used token; 422 and the rest keep the form so they can retry.
      if (err.status === 400) setTokenInvalido(true);
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  const solicitarNuevo = (
    <p className="tw-text-sm tw-text-ink-soft tw-m-0">
      <Link to="/olvide-contrasena" className={linkClass}>Solicita un nuevo enlace</Link>
    </p>
  );

  let contenido;
  if (!token) {
    contenido = (
      <>
        <ErrorBox>El enlace no es válido: falta el código para restablecer tu contraseña.</ErrorBox>
        {solicitarNuevo}
      </>
    );
  } else if (listo) {
    contenido = (
      <>
        <StatusBox>Tu contraseña se actualizó correctamente.</StatusBox>
        <Button to="/Login" variant="dark" size="lg" className="tw-w-full">Iniciar sesión</Button>
      </>
    );
  } else if (tokenInvalido) {
    contenido = (
      <>
        <ErrorBox>{error}</ErrorBox>
        {solicitarNuevo}
      </>
    );
  } else {
    contenido = (
      <>
        {error && <ErrorBox>{error}</ErrorBox>}
        <form onSubmit={handleSubmit}>
          <Input
            label="Nueva contraseña"
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="tw-mb-4"
          />
          <Input
            label="Confirma tu contraseña"
            id="confirmacion"
            type="password"
            autoComplete="new-password"
            value={confirmacion}
            onChange={(e) => setConfirmacion(e.target.value)}
            required
            className="tw-mb-6"
          />
          <Button type="submit" variant="dark" size="lg" disabled={enviando} className="tw-w-full">
            {enviando ? "Guardando..." : "Restablecer contraseña"}
          </Button>
        </form>
      </>
    );
  }

  return (
    <AuthCard title="Nueva contraseña" focusKey={`${listo}-${tokenInvalido}`}>
      {contenido}
    </AuthCard>
  );
};

export default RestablecerContrasena;
