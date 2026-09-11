import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import {
  CheckCircle2,
  XCircle,
  AlertCircle,
  Filter,
  Camera,
  FileText,
  Calendar,
  User,
  ShieldCheck,
  RefreshCw,
  Search
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { api, Evidencia, Delegacion } from '../lib/api';

export default function VerificacionPage() {
  const [evidencias, setEvidencias] = useState<Evidencia[]>([]);
  const [delegaciones, setDelegaciones] = useState<any[]>([]);
  const [filtroDelegacion, setFiltroDelegacion] = useState<string>('todas');
  const [filtroEstado, setFiltroEstado] = useState<string>('PENDIENTE');
  const [busqueda, setBusqueda] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [observacionModal, setObservacionModal] = useState<{ id: number; decision: 'RECHAZADA' | 'CORRECCION'; codigo: string } | null>(null);
  const [motivoTexto, setMotivoTexto] = useState<string>('');

  const cargarEvidencias = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filtroDelegacion !== 'todas') params.delegacion = parseInt(filtroDelegacion, 10);
      if (filtroEstado !== 'todos') params.estado = filtroEstado;
      const data = await api.getEvidencias(params);
      setEvidencias(data);
      const dels = await api.getDelegaciones();
      setDelegaciones(dels);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarEvidencias();
  }, [filtroDelegacion, filtroEstado]);

  const handleValidar = async (id: number, decision: 'APROBADA' | 'RECHAZADA' | 'CORRECCION', observacion?: string) => {
    setActionLoading(id);
    try {
      await api.validarEvidencia(id, { decision, observacion });
      await cargarEvidencias();
      setObservacionModal(null);
      setMotivoTexto('');
    } catch (err: any) {
      alert(`Error validando evidencia: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const evidenciasFiltradas = evidencias.filter((ev) => {
    if (!busqueda) return true;
    return ev.codigo_verificador.toLowerCase().includes(busqueda.toLowerCase());
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Head>
        <title>Validación de Evidencias ("Check") | Matriz SGR</title>
      </Head>

      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6">
        {/* Cabecera */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 p-5 rounded-2xl border border-slate-800 shadow-lg">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider">
                Control de Calidad & Prevención de Fraude
              </span>
              <span className="text-xs text-slate-400">
                Botón de Validación "Check" para Delegados y Verificadores
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1">
              Bandeja de Validación de Fotografías y Evidencias
            </h1>
            <p className="text-xs text-slate-400">
              Cada foto posee un código alfanumérico único inmutable (ej. ORC711). Solo las evidencias <strong>APROBADAS</strong> otorgan puntos al semáforo de desempeño.
            </p>
          </div>

          <button
            onClick={cargarEvidencias}
            disabled={loading}
            className="self-start md:self-auto p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700 transition-colors flex items-center gap-2 text-xs font-bold"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
            <span>Actualizar Bandeja</span>
          </button>
        </div>

        {/* Barra de Filtros */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            {/* Filtro Delegación */}
            <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
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

            {/* Filtro Estado */}
            <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
              <span className="font-bold text-slate-400 uppercase">Estado:</span>
              <select
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value)}
                className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
              >
                <option value="todos" className="bg-slate-900">Todos los Estados</option>
                <option value="PENDIENTE" className="bg-slate-900">🟡 Pendientes de Validación</option>
                <option value="APROBADA" className="bg-slate-900">🟢 Aprobadas (Check)</option>
                <option value="RECHAZADA" className="bg-slate-900">🔴 Rechazadas</option>
                <option value="CORRECCION" className="bg-slate-900">🟠 Requiere Corrección</option>
              </select>
            </div>
          </div>

          {/* Búsqueda por Código Único */}
          <div className="relative w-full sm:w-64">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por código (ej. CIA711)..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl py-1.5 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500"
            />
          </div>
        </div>

        {/* Grid de Evidencias */}
        {evidenciasFiltradas.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
            <Camera size={40} className="mx-auto text-slate-600 mb-3" />
            <h3 className="text-base font-bold text-white">No se encontraron evidencias</h3>
            <p className="text-xs text-slate-400 mt-1">
              No hay fotografías registradas para el filtro seleccionado.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {evidenciasFiltradas.map((ev) => (
              <div
                key={ev.id}
                className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-700 transition-all flex flex-col shadow-lg"
              >
                {/* Visualizador de Foto */}
                <div className="relative h-48 bg-slate-950 flex items-center justify-center overflow-hidden">
                  <img
                    src={ev.archivo_foto || ev.url_foto_simulada || 'https://images.unsplash.com/photo-1541888946425-d0fbb1861564?auto=format&fit=crop&w=600&q=80'}
                    alt={`Evidencia ${ev.codigo_verificador}`}
                    className="w-full h-full object-cover"
                  />
                  {/* Badge de Código Único Inmutable */}
                  <div className="absolute top-2.5 left-2.5 bg-slate-950/90 backdrop-blur border border-amber-400/50 text-amber-300 font-mono font-black text-xs px-2.5 py-1 rounded-md shadow">
                    ID: {ev.codigo_verificador}
                  </div>

                  {/* Badge de Estado Actual */}
                  <div className="absolute top-2.5 right-2.5">
                    {ev.estado === 'APROBADA' && (
                      <span className="bg-emerald-600 text-white font-bold text-[11px] px-2.5 py-1 rounded-md shadow flex items-center gap-1">
                        <CheckCircle2 size={12} /> Aprobada
                      </span>
                    )}
                    {ev.estado === 'PENDIENTE' && (
                      <span className="bg-amber-600 text-white font-bold text-[11px] px-2.5 py-1 rounded-md shadow flex items-center gap-1">
                        <AlertCircle size={12} /> Pendiente
                      </span>
                    )}
                    {ev.estado === 'RECHAZADA' && (
                      <span className="bg-rose-600 text-white font-bold text-[11px] px-2.5 py-1 rounded-md shadow flex items-center gap-1">
                        <XCircle size={12} /> Rechazada
                      </span>
                    )}
                  </div>
                </div>

                {/* Detalles de la Evidencia */}
                <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between text-slate-400">
                      <span>Fecha Registro:</span>
                      <span className="font-semibold text-slate-200">
                        {new Date(ev.fecha_subida).toLocaleDateString()}
                      </span>
                    </div>

                    {ev.verificador_nombre && (
                      <div className="flex justify-between text-slate-400">
                        <span>Verificado por:</span>
                        <span className="font-bold text-white">{ev.verificador_nombre}</span>
                      </div>
                    )}

                    {ev.observacion && (
                      <div className="p-2.5 bg-slate-950/80 border border-slate-800 rounded-xl text-slate-300 mt-2">
                        <span className="font-bold text-amber-400 block mb-0.5">Observación del Delegado:</span>
                        "{ev.observacion}"
                      </div>
                    )}
                  </div>

                  {/* Botones de Validación del Delegado ("Check") */}
                  <div className="pt-3 border-t border-slate-800/80 flex items-center gap-2">
                    <button
                      onClick={() => handleValidar(ev.id, 'APROBADA', 'Fotografía validada conforme en terreno')}
                      disabled={actionLoading === ev.id || ev.estado === 'APROBADA'}
                      className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white font-bold py-2 px-3 rounded-xl text-xs flex items-center justify-center gap-1.5 shadow transition-all"
                    >
                      <CheckCircle2 size={15} />
                      <span>Check (Aprobar)</span>
                    </button>

                    <button
                      onClick={() => setObservacionModal({ id: ev.id, decision: 'RECHAZADA', codigo: ev.codigo_verificador })}
                      disabled={actionLoading === ev.id || ev.estado === 'RECHAZADA'}
                      className="bg-rose-600/20 hover:bg-rose-600 hover:text-white border border-rose-500/30 text-rose-300 font-bold py-2 px-3 rounded-xl text-xs flex items-center justify-center gap-1 transition-all"
                      title="Rechazar evidencia con motivo"
                    >
                      <XCircle size={15} />
                      <span>Rechazar</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal para Observación de Rechazo */}
        {observacionModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 max-w-md w-full p-6 rounded-2xl shadow-2xl space-y-4">
              <div className="flex items-center gap-2 text-rose-400 font-bold">
                <XCircle size={20} />
                <h3>Rechazar Evidencia {observacionModal.codigo}</h3>
              </div>
              <p className="text-xs text-slate-400">
                Ingrese el motivo técnico por el cual se rechaza la fotografía (ej. imagen no nítida, fuera de jurisdicción o sin relación al ticket).
              </p>

              <textarea
                value={motivoTexto}
                onChange={(e) => setMotivoTexto(e.target.value)}
                rows={3}
                required
                placeholder="Indique el motivo del rechazo..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-rose-500"
              />

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setObservacionModal(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={() => handleValidar(observacionModal.id, 'RECHAZADA', motivoTexto)}
                  disabled={!motivoTexto.trim()}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold"
                >
                  Confirmar Rechazo
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
