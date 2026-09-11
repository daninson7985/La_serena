import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import {
  ClipboardList,
  Plus,
  Clock,
  CheckCircle2,
  AlertTriangle,
  User,
  Building2,
  Calendar,
  ArrowRight,
  Filter
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { api, Compromiso, Delegacion, Usuario } from '../lib/api';

export default function TuboDeTrabajoPage() {
  const [compromisos, setCompromisos] = useState<Compromiso[]>([]);
  const [delegaciones, setDelegaciones] = useState<any[]>([]);
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [filtroDelegacion, setFiltroDelegacion] = useState<string>('todas');
  const [loading, setLoading] = useState<boolean>(true);
  const [showModal, setShowModal] = useState<boolean>(false);

  // Formulario nuevo compromiso
  const [nuevoForm, setNuevoForm] = useState({
    solicitante: '',
    delegacion: '',
    responsable: '',
    fecha_comprometida: '',
    area_apoyo: 'Operaciones',
    descripcion: '',
  });

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filtroDelegacion !== 'todas') params.delegacion = parseInt(filtroDelegacion, 10);
      const data = await api.getCompromisos(params);
      setCompromisos(data);
      const dels = await api.getDelegaciones();
      setDelegaciones(dels);
      const usrs = await api.getUsuarios();
      setUsuarios(usrs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, [filtroDelegacion]);

  const handleCambiarEstado = async (id: number, nuevoEstado: string) => {
    try {
      await api.cambiarEstadoCompromiso(id, { estado: nuevoEstado, observacion: `Cambio de estado a ${nuevoEstado}` });
      await cargarDatos();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  const handleCrearCompromiso = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        solicitante: nuevoForm.solicitante,
        delegacion: parseInt(nuevoForm.delegacion, 10),
        responsable: parseInt(nuevoForm.responsable, 10),
        fecha_comprometida: nuevoForm.fecha_comprometida,
        area_apoyo: nuevoForm.area_apoyo,
        descripcion: nuevoForm.descripcion,
        estado: 'EN_PROCESO',
      };
      const res = await fetch('http://127.0.0.1:8000/api/compromisos/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('Error al guardar compromiso');
      setShowModal(false);
      setNuevoForm({
        solicitante: '',
        delegacion: '',
        responsable: '',
        fecha_comprometida: '',
        area_apoyo: 'Operaciones',
        descripcion: '',
      });
      await cargarDatos();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const columnas = [
    { id: 'INGRESADO', titulo: 'Ingresado', color: 'border-blue-500/40 bg-blue-500/5' },
    { id: 'PENDIENTE', titulo: 'Pendiente', color: 'border-amber-500/40 bg-amber-500/5' },
    { id: 'EN_PROCESO', titulo: 'En Proceso', color: 'border-purple-500/40 bg-purple-500/5' },
    { id: 'REALIZADO', titulo: 'Realizado (Cerrado)', color: 'border-emerald-500/40 bg-emerald-500/5' },
  ];

  const hoy = new Date().toISOString().split('T')[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Head>
        <title>Tubo de Trabajo | Matriz SGR</title>
      </Head>

      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6">
        {/* Cabecera */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 p-5 rounded-2xl border border-slate-800 shadow-lg">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider">
                Gestión Operativa Diaria
              </span>
              <span className="text-xs text-slate-400">
                Agenda Colectiva & Tubo de Compromisos Ciudadanos
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1">
              Tubo de Trabajo de las Delegaciones
            </h1>
            <p className="text-xs text-slate-400">
              Seguimiento riguroso de solicitudes vecinales. Todo compromiso no cerrado con fecha vencida se destaca automáticamente en alerta.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Filtro Delegación */}
            <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs">
              <Filter size={13} className="text-slate-400" />
              <span className="font-bold text-slate-400 uppercase">Delegación:</span>
              <select
                value={filtroDelegacion}
                onChange={(e) => setFiltroDelegacion(e.target.value)}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
              >
                <option value="todas" className="bg-slate-900">Todas</option>
                {delegaciones.map((d) => (
                  <option key={d.id} value={d.id.toString()} className="bg-slate-900">
                    {d.nombre} ({d.codigo})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setShowModal(true)}
              className="bg-red-600 hover:bg-red-500 text-white font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-1.5 shadow-lg shadow-red-900/30 transition-all"
            >
              <Plus size={16} />
              <span>Nuevo Compromiso</span>
            </button>
          </div>
        </div>

        {/* Tablero Kanban de 4 Columnas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {columnas.map((col) => {
            const items = compromisos.filter((c) => c.estado === col.id);
            return (
              <div
                key={col.id}
                className={`border rounded-2xl p-4 flex flex-col min-h-[500px] ${col.color}`}
              >
                <div className="flex justify-between items-center pb-3 mb-3 border-b border-slate-800">
                  <h3 className="font-bold text-sm text-white">{col.titulo}</h3>
                  <span className="bg-slate-900 text-slate-300 font-mono text-xs px-2 py-0.5 rounded-full border border-slate-800">
                    {items.length}
                  </span>
                </div>

                <div className="space-y-3 flex-1 overflow-y-auto">
                  {items.map((item) => {
                    const esVencido = item.estado !== 'REALIZADO' && item.fecha_comprometida < hoy;
                    return (
                      <div
                        key={item.id}
                        className={`bg-slate-900 border rounded-xl p-3.5 shadow space-y-2 transition-all ${
                          esVencido ? 'border-rose-500/80 ring-1 ring-rose-500/50' : 'border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        {esVencido && (
                          <div className="inline-flex items-center gap-1 bg-rose-500/20 text-rose-300 text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                            <AlertTriangle size={11} /> ¡Compromiso Vencido!
                          </div>
                        )}

                        <div className="text-xs font-bold text-white leading-tight">
                          {item.solicitante}
                        </div>

                        <p className="text-[11px] text-slate-300 leading-snug line-clamp-3">
                          {item.descripcion}
                        </p>

                        <div className="space-y-1 pt-2 border-t border-slate-800/80 text-[10px] text-slate-400">
                          <div className="flex justify-between">
                            <span>Delegación:</span>
                            <strong className="text-slate-200">{item.delegacion_codigo || 'Central'}</strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Responsable:</span>
                            <strong className="text-slate-200">{item.responsable_nombre || 'No asignado'}</strong>
                          </div>
                          <div className="flex justify-between">
                            <span>Fecha Límite:</span>
                            <strong className={esVencido ? 'text-rose-400 font-bold' : 'text-slate-200'}>
                              {item.fecha_comprometida}
                            </strong>
                          </div>
                        </div>

                        {/* Selector de Transición de Estado */}
                        <div className="pt-2 flex items-center justify-between gap-2">
                          <select
                            value={item.estado}
                            onChange={(e) => handleCambiarEstado(item.id, e.target.value)}
                            className="w-full bg-slate-950 border border-slate-800 text-[11px] font-semibold text-white rounded-lg p-1 focus:outline-none cursor-pointer"
                          >
                            <option value="INGRESADO">Mover a: Ingresado</option>
                            <option value="PENDIENTE">Mover a: Pendiente</option>
                            <option value="EN_PROCESO">Mover a: En Proceso</option>
                            <option value="REALIZADO">Mover a: Realizado</option>
                          </select>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Modal Nuevo Compromiso */}
        {showModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 max-w-lg w-full p-6 rounded-2xl shadow-2xl space-y-4">
              <div className="flex items-center gap-2 text-white font-bold text-base">
                <ClipboardList size={20} className="text-red-500" />
                <h3>Ingresar Solicitud al Tubo de Trabajo</h3>
              </div>

              <form onSubmit={handleCrearCompromiso} className="space-y-3 text-xs">
                <div>
                  <label className="block font-bold text-slate-300 uppercase mb-1">
                    Solicitante (Vecino u Organización Anonimizado)
                  </label>
                  <input
                    type="text"
                    required
                    value={nuevoForm.solicitante}
                    onChange={(e) => setNuevoForm({ ...nuevoForm, solicitante: e.target.value })}
                    placeholder="Ej. Junta de Vecinos El Olivar"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-red-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-bold text-slate-300 uppercase mb-1">Delegación</label>
                    <select
                      required
                      value={nuevoForm.delegacion}
                      onChange={(e) => setNuevoForm({ ...nuevoForm, delegacion: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-red-500"
                    >
                      <option value="">Seleccione...</option>
                      {delegaciones.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.nombre} ({d.codigo})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-bold text-slate-300 uppercase mb-1">Responsable</label>
                    <select
                      required
                      value={nuevoForm.responsable}
                      onChange={(e) => setNuevoForm({ ...nuevoForm, responsable: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-red-500"
                    >
                      <option value="">Seleccione...</option>
                      {usuarios.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.first_name} {u.last_name} ({u.delegacion_codigo || 'Central'})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-bold text-slate-300 uppercase mb-1">Fecha Comprometida</label>
                    <input
                      type="date"
                      required
                      value={nuevoForm.fecha_comprometida}
                      onChange={(e) => setNuevoForm({ ...nuevoForm, fecha_comprometida: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-red-500"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-300 uppercase mb-1">Área de Apoyo</label>
                    <input
                      type="text"
                      value={nuevoForm.area_apoyo}
                      onChange={(e) => setNuevoForm({ ...nuevoForm, area_apoyo: e.target.value })}
                      placeholder="Ej. Operaciones, Obras"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-red-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-bold text-slate-300 uppercase mb-1">Descripción del Requerimiento</label>
                  <textarea
                    required
                    rows={3}
                    value={nuevoForm.descripcion}
                    onChange={(e) => setNuevoForm({ ...nuevoForm, descripcion: e.target.value })}
                    placeholder="Detalles del compromiso asumido con la comunidad..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none focus:border-red-500"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-semibold"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl font-bold"
                  >
                    Guardar Compromiso
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
