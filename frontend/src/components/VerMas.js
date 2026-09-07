import React from 'react';
import { Link } from 'react-router-dom'

const VerMas = ({ title, description }) => {
    return (
        <div className="col-md-6 mb-4">
        <h5 className="fw-bold">{title}</h5>
        <p>{description}</p>
        <Link to="/Login" className="btn btn-outline-dark">Ver más</Link>
        </div>
    );
};

export default VerMas;