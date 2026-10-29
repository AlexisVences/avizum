import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createUser } from "../services/userService";
import Navbar from "../components/Navbar";
import logo from "../assets/logo.png";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import authService from "../services/authService";
import GoogleSignInButton, { GOOGLE_CLIENT_ID } from "../components/GoogleSignInButton";

const SignUp = () => {
    const [formData, setFormData] = useState({
        nombre: '',
        apellido: '',
        email: '',
        password: '',
        confirmPassword: '',
    });
    const [accepted, setAccepted] = useState(false);
    const [termsError, setTermsError] = useState('');
    const [registered, setRegistered] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleGoogle = async (credential) => {
        setError('');
        try {
            await authService.loginWithGoogle(credential);
            navigate(authService.getCurrentUser()?.rol === 'admin' ? '/admin' : '/Bienvenida');
        } catch (err) {
            setError(err.message);
        }
    };

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

        if (!accepted) {
            setTermsError('Debes aceptar los Términos de uso y el Aviso de privacidad para crear tu cuenta.');
            return;
        }

        setLoading(true);
        try {
            await createUser({ ...formData, acceptedTerms: true });
            setRegistered(true);
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

                        {registered ? (
                            <div role="status" className="tw-text-sm tw-text-ink">
                                <p className="tw-mt-0 tw-mb-4">
                                    Cuenta creada. Te enviamos un correo para verificar tu cuenta.
                                </p>
                                <Link to="/Login" className="tw-font-semibold tw-text-azul hover:tw-text-magenta tw-no-underline">
                                    Ir a iniciar sesión
                                </Link>
                            </div>
                        ) : (
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
                                className="tw-mb-4"
                            />

                            <div className="tw-mb-6">
                                <div className="tw-flex tw-items-start tw-gap-2">
                                    <input
                                        id="acceptTerms"
                                        type="checkbox"
                                        checked={accepted}
                                        onChange={(e) => { setAccepted(e.target.checked); if (e.target.checked) setTermsError(''); }}
                                        aria-required="true"
                                        aria-invalid={termsError ? 'true' : 'false'}
                                        aria-describedby={termsError ? 'acceptTerms-error' : undefined}
                                        className="tw-mt-1"
                                    />
                                    <label htmlFor="acceptTerms" className="tw-text-sm tw-text-ink">
                                        He leído y acepto los{" "}
                                        <a href="/terminos" target="_blank" rel="noopener noreferrer" className="tw-font-semibold tw-text-azul hover:tw-text-magenta">Términos de uso</a>
                                        {" "}y el{" "}
                                        <a href="/Aviso-legal" target="_blank" rel="noopener noreferrer" className="tw-font-semibold tw-text-azul hover:tw-text-magenta">Aviso de privacidad</a>
                                    </label>
                                </div>
                                {termsError && (
                                    <p id="acceptTerms-error" role="alert" className="tw-text-danger tw-text-xs tw-mt-1 tw-mb-0">
                                        {termsError}
                                    </p>
                                )}
                            </div>

                            <Button type="submit" variant="dark" size="lg" disabled={loading} className="tw-w-full">
                                {loading ? 'Creando cuenta...' : 'Crear cuenta'}
                            </Button>
                        </form>
                        )}

                        {!registered && GOOGLE_CLIENT_ID && (
                            <>
                                <div className="tw-flex tw-items-center tw-gap-3 tw-my-5 tw-text-xs tw-text-ink-soft">
                                    <span className="tw-h-px tw-flex-1 tw-bg-rule" />o<span className="tw-h-px tw-flex-1 tw-bg-rule" />
                                </div>
                                <GoogleSignInButton onCredential={handleGoogle} text="signup_with" />
                            </>
                        )}

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
