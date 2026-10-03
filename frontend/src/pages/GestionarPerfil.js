import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { FiEdit2 } from "react-icons/fi";
import NavBar2 from "../components/NavBar2";
import Footer from "../components/Footer";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import { updateUser } from "../services/userService";
import authService from "../services/authService";

const Perfil = () => {
    const storedUser = authService.getCurrentUser();
    const userId = storedUser?.id;

    const [userData, setUserData] = useState({ nombre: "", apellido: "", correo: "" });
    const [editando, setEditando] = useState({ nombre: false, apellido: false });
    const [inputs, setInputs] = useState({ nombre: "", apellido: "" });
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] = useState(null);

    useEffect(() => {
        const user = authService.getCurrentUser();
        if (user) {
            setUserData({
                nombre: user.nombre || "",
                apellido: user.apellido || "",
                correo: user.correo || "",
            });
            setInputs({ nombre: user.nombre || "", apellido: user.apellido || "" });
        }
    }, []);

    const handleChange = (e) => {
        setInputs({ ...inputs, [e.target.name]: e.target.value });
    };

    const alternarEdicion = (campo) => {
        setEditando({ ...editando, [campo]: !editando[campo] });
    };

    const guardarCambios = async () => {
        setError(null);
        if (!userId) {
            setError("No se puede actualizar el usuario sin ID");
            return;
        }

        try {
            const updatedData = {
                nombre: inputs.nombre,
                apellido: inputs.apellido,
                rol: storedUser.rol,
                email: storedUser.correo,
            };
            const response = await updateUser(storedUser.correo, updatedData);

            if (!response) {
                throw new Error("No se recibió respuesta del servidor");
            }

            setUserData({ ...userData, nombre: inputs.nombre, apellido: inputs.apellido });
            localStorage.setItem(
                "user",
                JSON.stringify({ ...storedUser, nombre: inputs.nombre, apellido: inputs.apellido })
            );
            setEditando({ nombre: false, apellido: false });
            setSuccessMessage("Cambios guardados correctamente");
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setError(err.message || "Error al guardar los cambios");
            console.error("Update error:", err);
        }
    };

    const cambiosPendientes =
        inputs.nombre !== userData.nombre || inputs.apellido !== userData.apellido;

    const campoEditable = (campo, etiqueta) => (
        <div className="tw-flex tw-items-end tw-gap-2.5">
            <Input
                label={etiqueta}
                name={campo}
                value={inputs[campo]}
                onChange={handleChange}
                disabled={!editando[campo]}
                className="tw-flex-1 tw-min-w-0"
            />
            <button
                type="button"
                aria-label={`Editar ${campo}`}
                aria-pressed={editando[campo]}
                onClick={() => alternarEdicion(campo)}
                className={`tw-shrink-0 tw-inline-flex tw-h-[42px] tw-w-[42px] tw-items-center tw-justify-center tw-rounded tw-border tw-transition-colors ${
                    editando[campo]
                        ? "tw-border-azul tw-bg-azul/5 tw-text-azul"
                        : "tw-border-rule tw-bg-paper-raised tw-text-ink-soft hover:tw-border-ink/40 hover:tw-text-ink"
                }`}
            >
                <FiEdit2 aria-hidden="true" />
            </button>
        </div>
    );

    return (
        <>
            <NavBar2 />
            <main className="tw-flex-1 tw-pt-16">
                <div className="tw-px-4 tw-py-12">
                    <div className="tw-mx-auto tw-max-w-lg">
                        <span className="tw-block tw-text-center tw-font-mono tw-text-[11.5px] tw-uppercase tw-tracking-widest tw-text-azul tw-font-bold tw-mb-3.5">
                            Tu cuenta
                        </span>
                        <h1 className="tw-font-display tw-text-center tw-text-3xl tw-font-semibold tw-text-ink tw-mb-3">
                            Gestión de perfil
                        </h1>

                        {successMessage && (
                            <div
                                role="status"
                                className="tw-mb-4 tw-bg-verde/10 tw-border tw-border-verde/30 tw-text-verde tw-text-sm tw-font-semibold tw-text-center tw-rounded tw-px-4 tw-py-3 tw-animate-fade-in-up"
                            >
                                {successMessage}
                            </div>
                        )}

                        {(error || !storedUser) && (
                            <div
                                role="alert"
                                className="tw-mb-4 tw-bg-danger/5 tw-border tw-border-danger/30 tw-text-danger tw-text-sm tw-text-center tw-rounded tw-px-4 tw-py-3 tw-animate-fade-in-up"
                            >
                                {error || "No hay usuario autenticado"}
                            </div>
                        )}

                        {storedUser ? (
                            <div className="tw-bg-paper-raised tw-border tw-border-rule tw-rounded-lg tw-shadow-sm tw-p-6">
                                <div className="tw-pb-5 tw-mb-5 tw-border-b tw-border-rule">
                                    <p className="tw-font-display tw-text-xl tw-font-semibold tw-text-ink tw-m-0">
                                        {userData.nombre} {userData.apellido}
                                    </p>
                                    <p className="tw-text-sm tw-text-ink-soft tw-m-0 tw-mt-0.5">Usuario registrado</p>
                                </div>

                                <div className="tw-flex tw-flex-col tw-gap-4">
                                    {campoEditable("nombre", "Nombre")}
                                    {campoEditable("apellido", "Apellido")}
                                    <Input label="Correo electrónico" type="email" value={userData.correo} disabled readOnly />
                                </div>

                                {cambiosPendientes && (
                                    <div className="tw-mt-6 tw-flex tw-justify-end">
                                        <Button variant="dark" onClick={guardarCambios}>
                                            Guardar cambios
                                        </Button>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <p className="tw-text-center">
                                <Link to="/Login" className="tw-text-azul hover:tw-text-magenta tw-font-semibold">
                                    Iniciar sesión →
                                </Link>
                            </p>
                        )}
                    </div>
                </div>
            </main>
            <Footer className="tw-pt-0" />
        </>
    );
};

export default Perfil;
