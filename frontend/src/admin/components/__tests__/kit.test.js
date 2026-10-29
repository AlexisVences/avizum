import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import PageHeader from '../PageHeader';
import Skeleton from '../Skeleton';
import EmptyState from '../EmptyState';
import ErrorState from '../ErrorState';
import ConfirmDialog from '../ConfirmDialog';
import StatusBadge from '../StatusBadge';
import Pagination from '../Pagination';

// jsdom no implementa HTMLDialogElement.showModal/close: doble mínimo.
beforeAll(() => {
    window.HTMLDialogElement.prototype.showModal = function showModal() {
        this.setAttribute('open', '');
    };
    window.HTMLDialogElement.prototype.close = function close() {
        this.removeAttribute('open');
    };
});

describe('PageHeader', () => {
    test('muestra el título como h1, la descripción y las acciones', () => {
        render(<PageHeader title="Personas" description="Gestiona cuentas" actions={<button>Nueva</button>} />);
        expect(screen.getByRole('heading', { level: 1, name: 'Personas' })).toBeInTheDocument();
        expect(screen.getByText('Gestiona cuentas')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Nueva' })).toBeInTheDocument();
    });
});

describe('Skeleton', () => {
    test('anuncia Cargando', () => {
        render(<Skeleton />);
        expect(screen.getByRole('status', { name: 'Cargando' })).toBeInTheDocument();
    });
});

describe('EmptyState', () => {
    test('muestra título, pista y acción', () => {
        render(<EmptyState title="Sin personas" hint="Prueba otra búsqueda" action={<button>Limpiar</button>} />);
        expect(screen.getByText('Sin personas')).toBeInTheDocument();
        expect(screen.getByText('Prueba otra búsqueda')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Limpiar' })).toBeInTheDocument();
    });
});

describe('ErrorState', () => {
    test('muestra el mensaje y llama onRetry al pulsar Reintentar', () => {
        const onRetry = jest.fn();
        render(<ErrorState message="No se pudo cargar" onRetry={onRetry} />);
        expect(screen.getByText('No se pudo cargar')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
        expect(onRetry).toHaveBeenCalledTimes(1);
    });
});

describe('StatusBadge', () => {
    test('el texto acompaña al color', () => {
        render(<StatusBadge tone="ok">Activa</StatusBadge>);
        expect(screen.getByText('Activa')).toBeInTheDocument();
    });
});

describe('ConfirmDialog', () => {
    const base = {
        title: 'Desactivar cuenta',
        body: 'La persona ya no podrá entrar.',
        confirmLabel: 'Desactivar cuenta',
    };

    test('abre con role dialog y confirma', () => {
        const onConfirm = jest.fn();
        render(<ConfirmDialog open {...base} onConfirm={onConfirm} onCancel={jest.fn()} />);
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Desactivar cuenta' }));
        expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    test('Escape llama onCancel', () => {
        const onCancel = jest.fn();
        render(<ConfirmDialog open {...base} onConfirm={jest.fn()} onCancel={onCancel} />);
        fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
        expect(onCancel).toHaveBeenCalledTimes(1);
    });

    test('con requireText el botón queda deshabilitado hasta que coincide', () => {
        const onConfirm = jest.fn();
        render(
            <ConfirmDialog open {...base} tone="danger" requireText="ana@x.mx" onConfirm={onConfirm} onCancel={jest.fn()} />
        );
        const boton = screen.getByRole('button', { name: 'Desactivar cuenta' });
        expect(boton).toBeDisabled();
        fireEvent.change(screen.getByRole('textbox'), { target: { value: 'ana@x.m' } });
        expect(boton).toBeDisabled();
        fireEvent.change(screen.getByRole('textbox'), { target: { value: 'ana@x.mx' } });
        expect(boton).toBeEnabled();
        fireEvent.click(boton);
        expect(onConfirm).toHaveBeenCalledTimes(1);
    });

    test('cerrado no muestra el diálogo', () => {
        render(<ConfirmDialog open={false} {...base} onConfirm={jest.fn()} onCancel={jest.fn()} />);
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
});

describe('Pagination', () => {
    test('page 2, pageSize 20, total 45 muestra el rango', () => {
        const onChange = jest.fn();
        render(<Pagination page={2} pageSize={20} total={45} onChange={onChange} />);
        expect(screen.getByText('Mostrando 21–40 de 45')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
        expect(onChange).toHaveBeenCalledWith(3);
        fireEvent.click(screen.getByRole('button', { name: 'Anterior' }));
        expect(onChange).toHaveBeenCalledWith(1);
    });

    test('deshabilita los extremos', () => {
        const { rerender } = render(<Pagination page={1} pageSize={20} total={45} onChange={jest.fn()} />);
        expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled();
        rerender(<Pagination page={3} pageSize={20} total={45} onChange={jest.fn()} />);
        expect(screen.getByText('Mostrando 41–45 de 45')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled();
    });

    test('total 0 muestra Sin resultados', () => {
        render(<Pagination page={1} pageSize={20} total={0} onChange={jest.fn()} />);
        expect(screen.getByText('Sin resultados')).toBeInTheDocument();
    });
});

describe('Pagination fuera de rango', () => {
    test('una página mayor que la última muestra el último rango real', () => {
        render(<Pagination page={5} pageSize={20} total={45} onChange={() => {}} />);
        expect(screen.getByText('Mostrando 41–45 de 45')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled();
    });
});

describe('ConfirmDialog ids', () => {
    test('dos diálogos tienen ids de título distintos', () => {
        render(
            <>
                <ConfirmDialog open={false} title="Uno" body="a" confirmLabel="Sí" onConfirm={() => {}} onCancel={() => {}} />
                <ConfirmDialog open={false} title="Dos" body="b" confirmLabel="Sí" onConfirm={() => {}} onCancel={() => {}} />
            </>
        );
        const ids = screen.getAllByRole('heading', { level: 2, hidden: true }).map((h) => h.id);
        expect(ids[0]).toBeTruthy();
        expect(new Set(ids).size).toBe(2);
        const labelled = Array.from(document.querySelectorAll('dialog')).map((d) => d.getAttribute('aria-labelledby'));
        expect(labelled).toEqual(ids);
    });
});
