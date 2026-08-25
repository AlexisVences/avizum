import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { FaTrash, FaUser, FaEnvelope, FaSearch, FaEdit } from "react-icons/fa";
import Footer from "../components/Footer";
import NavBarAdmin from "../components/NavBarAdmin";
import "../styles/AdministrarUsuario.css";
import { getAllUsers, updateUserRole, deleteUser } from "../services/userService";

const AdministrarUsuarios = () => {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [userToDelete, setUserToDelete] = useState(null);
  const [userToEdit, setUserToEdit] = useState(null);
  const [editData, setEditData] = useState({ nombre: "", apellido: "", email: "", rol: "" });

  useEffect(() => {
  const fetchUsers = async () => {
    try {
      const data = await getAllUsers();
      console.log("Usuarios cargados:", data);
      setUsers(data.clientes || []);
    } catch (error) {
      console.error("Error al obtener usuarios:", error);
      setUsers([]);
    }
  };

  fetchUsers();
}, []);

  const filteredUsers = users.filter((u) => {
    const searchTerm = search.toLowerCase();
    return (
      `${u.nombre || ''} ${u.apellido || ''}`.toLowerCase().includes(searchTerm) ||
      (u.email || u.correo || '').toLowerCase().includes(searchTerm)
    );
  });

  const eliminarUsuario = async () => {
    try {
      if (userToDelete) {
        await deleteUser(userToDelete.usuario); // Asegúrate que este campo es el identificador
        setUsers(users.filter((u) => u.usuario !== userToDelete.usuario));
        setUserToDelete(null);
      }
    } catch (error) {
      console.error("Error al eliminar usuario:", error);
    }
  };

  const abrirModalEdicion = (user) => {
    setUserToEdit(user);
    setEditData({ usuario:user.email, nombre: user.nombre, apellido: user.apellido, email: user.email, rol: user.rol });
  };

  const guardarCambios = async () => {
    try {
      await updateUserRole(userToEdit.id, { role: editData.rol });
      setUsers(users.map((u) =>
        u.id === userToEdit.id ? { ...u, rol: editData.rol } : u
      ));
      setUserToEdit(null);
    } catch (error) {
      console.error("Error al actualizar usuario:", error);
    }
  };

  return (
    <>
      <NavBarAdmin />
      <div className="page-container">
        <div className="container" style={{ paddingTop: '12rem' }}>
          <motion.h1
            className="text-center fw-bold mb-4"
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            Administrar Usuarios
          </motion.h1>

          <motion.div
            className="d-flex justify-content-between align-items-center mb-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            style={{ paddingTop: "3rem" }}
          >
            <div className="input-group" style={{ maxWidth: "350px" }}>
              <span className="input-group-text">
                <FaSearch />
              </span>
              <input
                type="text"
                className="form-control"
                placeholder="Buscar usuario"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <span className="text-muted">{filteredUsers.length} usuario(s)</span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <div className="table-responsive shadow rounded">
              <table className="table table-striped align-middle">
                <thead className="table-primary">
                  <tr>
                    <th><FaUser /> Nombre</th>
                    <th>Apellido</th>
                    <th><FaEnvelope /> Correo</th>
                    <th>Rol</th>
                    <th>Consultas</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id}>
                      <td>{user.nombre}</td>
                      <td>{user.apellido}</td>
                      <td>{user.email}</td>
                      <td>{user.rol}</td>
                      <td>{user.consultas}</td>
                      <td>
                        <div className="d-flex gap-2">
                          <button
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => abrirModalEdicion(user)} 
                          >
                            <FaEdit className="me-1" /> Editar
                          </button>
                          <button
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => setUserToDelete(user)}
                          >
                            <FaTrash /> Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {filteredUsers.length === 0 && (
                    <tr>
                      <td colSpan="6" className="text-center text-muted">
                        No se encontraron usuarios.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Modal de confirmación de eliminación */}
          {userToDelete && (
            <div className="modal fade show d-block" tabIndex="-1" style={{ backgroundColor: "rgba(0,0,0,0.5)" }}>
              <div className="modal-dialog modal-dialog-centered">
                <div className="modal-content">
                  <div className="modal-header bg-danger text-white">
                    <h5 className="modal-title">Confirmar eliminación</h5>
                    <button type="button" className="btn-close" onClick={() => setUserToDelete(null)}></button>
                  </div>
                  <div className="modal-body">
                    ¿Estás seguro de que deseas eliminar al usuario <strong>{userToDelete.nombre} {userToDelete.apellido}</strong>?
                  </div>
                  <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={() => setUserToDelete(null)}>Cancelar</button>
                    <button className="btn btn-danger" onClick={eliminarUsuario}>Eliminar</button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Modal de edición */}
          {userToEdit && (
            <div className="modal fade show d-block" tabIndex="-1" style={{ backgroundColor: "rgba(0,0,0,0.5)" }}>
              <div className="modal-dialog modal-dialog-centered">
                <div className="modal-content">
                  <div className="modal-header bg-primary text-white">
                    <h5 className="modal-title">Editar usuario</h5>
                    <button type="button" className="btn-close" onClick={() => setUserToEdit(null)}></button>
                  </div>
                  <div className="modal-body">
                    <div className="mb-3">
                      <label className="form-label">Nombre</label>
                      <input
                        type="text"
                        className="form-control"
                        value={editData.nombre}
                        onChange={(e) => setEditData({ ...editData, nombre: e.target.value })}
                      />
                    </div>
                    <div className="mb-3">
                      <label className="form-label">Apellido</label>
                      <input
                        type="text"
                        className="form-control"
                        value={editData.apellido}
                        onChange={(e) => setEditData({ ...editData, apellido: e.target.value })}
                      />
                    </div>
                    <div className="mb-3">
                      <label className="form-label">Correo</label>
                      <input
                        type="email"
                        className="form-control"
                        value={editData.email}
                        onChange={(e) => setEditData({ ...editData, email: e.target.value ,usuario: e.target.value})}
                      />
                    </div>
                    <div className="mb-3">
                      <label className="form-label">Rol</label>
                      <input
                        type="rol"
                        className="form-control"
                        value={editData.rol}
                        onChange={(e) => setEditData({ ...editData, rol: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={() => setUserToEdit(null)}>Cancelar</button>
                    <button className="btn btn-primary" onClick={guardarCambios}>Guardar cambios</button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </>
  );
};

export default AdministrarUsuarios;
