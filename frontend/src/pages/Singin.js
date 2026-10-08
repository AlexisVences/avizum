import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createUser } from "../services/userService";
import Navbar from "../components/Navbar";
import logo from "../assets/logo.png";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";

const SignUp = () => {
    const [formData, setFormData] = useState({
        nombre: '',
        apellido: '',
        email: '',
        password: '',
        confirmPassword: '',
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
        setError('');

        if (formData.password !== formData.confirmPassword) {
            setError('Las contraseñas no coinciden');
            return;
        }

        setLoading(true);
        try {
            // Usamos el servicio importado en lugar de fetch directo
            await createUser(formData);

            // Redirigir a la página de login después de crear el usuario
            navigate('/Login');
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
                            <img src={logo} alt="Avizum" className="tw-h-8 tw-w-auto tw-shrink-0" />
                            <h1 className="tw-font-display tw-text-2xl tw-font-semibold tw-text-ink tw-m-0">
                                Crear cuenta
                            </h1>
                        </div>

                        {error && (
                            <div className="tw-bg-danger/5 tw-border tw-border-danger/20 tw-text-danger tw-text-sm tw-rounded tw-px-3.5 tw-py-2.5 tw-mb-4">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            <div className="tw-grid tw-grid-cols-2 tw-gap-3 tw-mb-4">
                                <Input label="Nombre" id="nombre" value={formData.nombre} onChange={handleChange} required />
                                <Input label="Apellido" id="apellido" value={formData.apellido} onChange={handleChange} required />
                            </div>
                            <Input
                                label="Correo electrónico"
                                id="email"
                                type="email"
                                value={formData.email}
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
                                minLength={8}
                                className="tw-mb-1"
                            />
                            <p className="tw-text-xs tw-text-ink-soft tw-mt-0 tw-mb-4">
                                Mínimo 8 caracteres.
                            </p>
                            <Input
                                label="Confirmar contraseña"
                                id="confirmPassword"
                                type="password"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                required
                                className="tw-mb-6"
                            />

                            <Button type="submit" variant="dark" size="lg" disabled={loading} className="tw-w-full">
                                {loading ? 'Creando cuenta...' : 'Crear cuenta'}
                            </Button>
                        </form>

                        <p className="tw-text-center tw-text-sm tw-text-ink-soft tw-mt-6 tw-mb-0">
                            ¿Ya tienes cuenta?{" "}
                            <Link to="/Login" className="tw-font-semibold tw-text-azul hover:tw-text-magenta tw-no-underline">
                                Inicia sesión
                            </Link>
                        </p>
                    </div>
                </div>
            </main>
        </>
    );
};

export default SignUp;
