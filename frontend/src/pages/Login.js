// src/pages/LoginPage.jsx
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import authService from "../services/authService";
import Navbar from "../components/Navbar";
import logo from "../assets/logo.png";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";

const LoginPage = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await authService.login(formData);
      // Obtener el usuario actual después del login
      const currentUser = authService.getCurrentUser();

      // Redirigir según el rol
      if (currentUser && currentUser.rol === 'admin') {
        navigate('/BienvenidaAdmin');
      } else {
        navigate('/Bienvenida');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <main className="tw-pt-16">
        <div className="tw-min-h-[calc(100vh-4rem)] tw-bg-gris tw-flex tw-items-center tw-justify-center tw-px-4 tw-py-10">
          <div className="tw-w-full tw-max-w-md tw-bg-paper-raised tw-border tw-border-rule tw-rounded-lg tw-shadow-sm tw-p-8">
            <div className="tw-flex tw-items-center tw-gap-2.5 tw-mb-6">
              <img src={logo} alt="Abogadazo" className="tw-h-8 tw-w-auto tw-shrink-0" />
              <h1 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-m-0">
                Inicia sesión
              </h1>
            </div>

            {error && (
              <div className="tw-bg-red-50 tw-border tw-border-red-200 tw-text-red-700 tw-text-sm tw-rounded tw-px-3.5 tw-py-2.5 tw-mb-4">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <Input
                label="Correo electrónico"
                id="username"
                type="text"
                value={formData.username}
                onChange={handleChange}
                required
                className="tw-mb-4"
              />
              <Input
                label="Contraseña"
                id="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="tw-mb-4"
              />

              <label className="tw-flex tw-items-center tw-gap-2 tw-text-sm tw-text-ink-soft tw-mb-6 tw-cursor-pointer">
                <input
                  type="checkbox"
                  id="rememberMe"
                  className="tw-rounded tw-border-rule tw-text-azul focus:tw-ring-azul/30"
                />
                Mantenerme conectado en este dispositivo
              </label>

              <Button type="submit" variant="dark" size="lg" disabled={loading} className="tw-w-full">
                {loading ? 'Cargando...' : 'Iniciar sesión'}
              </Button>
            </form>

            <p className="tw-text-center tw-text-sm tw-text-ink-soft tw-mt-6 tw-mb-0">
              ¿No tienes cuenta?{" "}
              <Link to="/Sing-in" className="tw-font-semibold tw-text-azul hover:tw-text-magenta tw-no-underline">
                Regístrate
              </Link>
            </p>
          </div>
        </div>
      </main>
    </>
  );
};

export default LoginPage;
