import React, { useState } from "react";
import { Link } from "react-router-dom";
import AuthCard, { ErrorBox, StatusBox, linkClass } from "../components/AuthCard";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { forgotPassword } from "../services/emailAccountService";

const OlvideContrasena = () => {
  const [email, setEmail] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await forgotPassword(email.trim());
      setEnviado(true);
    } catch (err) {
      // Only transport/rate-limit failures reach here; the API answers the same either way.
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <AuthCard title="Recupera tu contraseña" focusKey={enviado}>
      {enviado ? (
        <StatusBox>Si el correo está registrado, te enviamos instrucciones</StatusBox>
      ) : (
        <>
          {error && <ErrorBox>{error}</ErrorBox>}
          <form onSubmit={handleSubmit}>
            <Input
              label="Correo electrónico"
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="tw-mb-6"
            />
            <Button type="submit" variant="dark" size="lg" disabled={enviando} className="tw-w-full">
              {enviando ? "Enviando..." : "Enviar instrucciones"}
            </Button>
          </form>
        </>
      )}
      <p className="tw-text-center tw-text-sm tw-mt-6 tw-mb-0">
        <Link to="/Login" className={linkClass}>Volver a iniciar sesión</Link>
      </p>
    </AuthCard>
  );
};

export default OlvideContrasena;
