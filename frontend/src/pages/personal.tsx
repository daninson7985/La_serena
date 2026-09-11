import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import Link from 'next/link';
import {
  User,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  PlusCircle,
  FileCheck2,
  ListTodo,
  TrendingUp,
  Activity
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { SemaforoBadge } from '../components/SemaforoBadge';
import { api, MetricasFuncionario, Usuario } from '../lib/api';

export default function DashboardPersonalPage() {
  const router = useRouter();
  const { id } = router.query;
  const [metricas, setMetricas] = useState<MetricasFuncionario | null>(null);
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [selectedFuncionarioId, setSelectedFuncionarioId] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      setError(null);
      try {
        const usrs = await api.getUsuarios({ rol: 'FUNCIONARIO' });
        setUsuarios(usrs);

        let targetId: number | null = null;
        if (id) {
          targetId = parseInt(id as string, 10);
        } else {
          // Buscar usuario en sesión
          const stored = localStorage.getItem('matriz_sgr_user');
          if (stored) {
            const u = JSON.parse(stored);
            if (u.rol === 'FUNCIONARIO') {
              targetId = u.id;
            }
          }
          if (!targetId && usrs.length > 0) {
            targetId = usrs[0].id;
          }
        }

        if (targetId) {
          setSelectedFuncionarioId(targetId);
          const data = await api.getMetricasFuncionario(targetId);
          setMetricas(data);
        }
      } catch (err: any) {
        setError(err.message || 'Error cargando datos personales.');
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [id]);

  const handleCambiarFuncionario = async (targetId: number) => {
    setSelectedFuncionarioId(targetId);
    setLoading(true);
    try {
      const data = await api.getMetricasFuncionario(targetId);
      setMetricas(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Head>
        <title>Dashboard Personal | Matriz SGR</title>
      </Head>

      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6">
        {/* Selector de funcionario para supervisión */}
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider">
              Ficha de Desempeño Individual
            </span>
            <span className="text-xs text-slate-400">
              Evaluación trimestral y cumplimiento por ítems
            </span>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs font-bold text-slate-400 uppercase">Consultar Funcionario:</label>
            <select
              value={selectedFuncionarioId || ''}
              onChange={(e) => handleCambiarFuncionario(parseInt(e.target.value, 10))}
              className="bg-slate-950 border border-slate-800 text-sm font-semibold text-white px-3 py-1.5 rounded-xl focus:outline-none"
            >
              {usuarios.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.first_name} {u.last_name} ({u.delegacion_codigo || 'Central'})
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-4 rounded-xl text-sm flex items-center gap-3">
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {metricas && (
          <>
            {/* Banner de Identidad y Semáforo Personal */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl relative overflow-hidden">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="bg-red-600 text-white font-bold px-2.5 py-0.5 rounded-md text-xs uppercase tracking-wider">
                      {metricas.delegacion} ({metricas.delegacion_codigo})
                    </span>
                    <span className="text-slate-400 text-xs font-mono">
                      Período: {metricas.periodo_nombre}
                    </span>
                  </div>

                  <h1 className="text-2xl md:text-3xl font-black text-white">
                    {metricas.nombre_completo}
                  </h1>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                    <span className="flex items-center gap-1.5 font-medium">
                      <User size={14} className="text-slate-400" /> Cargo: <strong>{metricas.cargo}</strong>
                    </span>
                    <span className="flex items-center gap-1.5 font-medium">
                      <Calendar size={14} className="text-slate-400" /> Días Transcurridos: <strong>{metricas.dias_transcurridos} / {metricas.dias_totales}</strong>
                    </span>
                    <span className="flex items-center gap-1.5 font-medium">
                      <Activity size={14} className="text-slate-400" /> Total Actividades: <strong>{metricas.total_actividades}</strong>
                    </span>
                  </div>
                </div>

                {/* Semáforo Personal & Porcentaje */}
                <div className="bg-slate-950/80 border border-slate-800 p-5 rounded-2xl flex items-center gap-5 shadow-inner">
                  <div className="text-right">
                    <div className="text-[11px] uppercase tracking-wider font-bold text-slate-400">
                      Cumplimiento Ponderado
                    </div>
                    <div className="text-3xl font-black text-white">
                      {metricas.total_ponderado_pct}%
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Meta acumulada esperada: <span className="font-bold text-amber-400">{metricas.meta_esperada_pct}%</span>
                    </div>
                  </div>

                  <div className="pl-4 border-l border-slate-800 flex flex-col items-center">
                    <SemaforoBadge color={metricas.semaforo_global} tamano="lg" />
                  </div>
                </div>
              </div>

              {/* Botón Flotante para Terreno */}
              <div className="mt-6 pt-4 border-t border-slate-800/80 flex justify-between items-center">
                <p className="text-xs text-slate-400">
                  * Únicamente las actividades con evidencia fotográfica validada con estado <strong>APROBADA</strong> suman a tu avance.
                </p>
                <Link
                  href="/terreno"
                  className="bg-red-600 hover:bg-red-500 text-white font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-red-900/30 transition-all"
                >
                  <PlusCircle size={15} />
                  <span>Nuevo Registro en Terreno (3 Clics)</span>
                </Link>
              </div>
            </div>

            {/* Desglose por Ítems de Medición (La Matriz Ponderada) */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="p-5 border-b border-slate-800 flex justify-between items-center">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <FileCheck2 size={18} className="text-red-500" />
                    Matriz de Cumplimiento por Ítem de Medición
                  </h3>
                  <p className="text-xs text-slate-400">
                    Cálculo individual de avance validado versus meta y su ponderador correspondiente (Tope 150%).
                  </p>
                </div>
                <div className="text-xs text-slate-400">
                  Meta esperada del día: <strong className="text-white">{metricas.meta_esperada_pct}%</strong>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                    <tr>
                      <th className="p-3.5">Ítem Medible</th>
                      <th className="p-3.5 text-center">Meta Trimestre</th>
                      <th className="p-3.5 text-center">Ponderador</th>
                      <th className="p-3.5 text-center">Avance Aprobado</th>
                      <th className="p-3.5 text-center">En Revisión</th>
                      <th className="p-3.5 text-center">Rechazadas</th>
                      <th className="p-3.5 text-center">% Cumplimiento</th>
                      <th className="p-3.5 text-center">Aporte Ponderado</th>
                      <th className="p-3.5 text-center">Semáforo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {metricas.items.map((item) => (
                      <tr key={item.item_id} className="hover:bg-slate-850/50 transition-colors">
                        <td className="p-3.5">
                          <div className="font-bold text-white">{item.nombre}</div>
                          <div className="text-[11px] text-slate-400">{item.unidad}</div>
                        </td>
                        <td className="p-3.5 text-center font-semibold text-slate-200">
                          {item.meta} {item.unidad}
                        </td>
                        <td className="p-3.5 text-center font-bold text-amber-400">
                          {item.ponderador}%
                        </td>
                        <td className="p-3.5 text-center font-bold text-emerald-400 text-sm">
                          {item.avance_aprobado}
                        </td>
                        <td className="p-3.5 text-center text-slate-400">
                          {item.evidencias_pendientes > 0 ? (
                            <span className="text-amber-400 font-semibold">{item.evidencias_pendientes}</span>
                          ) : (
                            0
                          )}
                        </td>
                        <td className="p-3.5 text-center text-slate-400">
                          {item.evidencias_rechazadas > 0 ? (
                            <span className="text-rose-400 font-semibold">{item.evidencias_rechazadas}</span>
                          ) : (
                            0
                          )}
                        </td>
                        <td className="p-3.5 text-center font-bold text-white text-sm">
                          {item.cumplimiento_pct}%
                        </td>
                        <td className="p-3.5 text-center font-extrabold text-white text-sm bg-slate-950/40">
                          {item.aporte_ponderado}%
                        </td>
                        <td className="p-3.5 text-center">
                          <SemaforoBadge color={item.semaforo} tamano="sm" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-950 font-bold text-white border-t border-slate-800">
                    <tr>
                      <td colSpan={7} className="p-3.5 text-right uppercase tracking-wider text-slate-400 text-xs">
                        Puntuación Total Ponderada Personal:
                      </td>
                      <td className="p-3.5 text-center text-base text-amber-300">
                        {metricas.total_ponderado_pct}%
                      </td>
                      <td className="p-3.5 text-center">
                        <SemaforoBadge color={metricas.semaforo_global} tamano="sm" />
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Tubo de Trabajo del Funcionario */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-white text-sm flex items-center gap-2">
                    <ListTodo size={16} className="text-blue-400" />
                    Compromisos en el Tubo de Trabajo
                  </h4>
                  <Link href="/tubo" className="text-xs text-blue-400 hover:underline">
                    Ver Todos &rarr;
                  </Link>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center pt-2">
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400">Total</div>
                    <div className="text-xl font-bold text-white">{metricas.compromisos.total}</div>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400">Realizados</div>
                    <div className="text-xl font-bold text-emerald-400">{metricas.compromisos.realizados}</div>
                  </div>
                  <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-400">Pendientes</div>
                    <div className="text-xl font-bold text-amber-400">{metricas.compromisos.pendientes}</div>
                  </div>
                </div>
                <div className="pt-2 text-xs text-slate-400 flex justify-between items-center">
                  <span>Tasa de efectividad:</span>
                  <span className="font-bold text-white">{metricas.compromisos.porcentaje_realizado}%</span>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
                <h4 className="font-bold text-white text-sm flex items-center gap-2">
                  <TrendingUp size={16} className="text-emerald-400" />
                  Métricas de Continuidad y Terreno (RF-030)
                </h4>
                <div className="space-y-2 text-xs pt-1">
                  <div className="flex justify-between text-slate-400">
                    <span>Promedio diario de registros:</span>
                    <strong className="text-white">{metricas.promedio_diario} act/día</strong>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Último registro validado:</span>
                    <strong className="text-white">{metricas.ultima_actividad ? new Date(metricas.ultima_actividad).toLocaleDateString() : 'Sin registros'}</strong>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Días sin ingresar actividades:</span>
                    <strong className={metricas.dias_sin_ingreso && metricas.dias_sin_ingreso > 2 ? 'text-amber-400' : 'text-emerald-400'}>
                      {metricas.dias_sin_ingreso !== null ? `${metricas.dias_sin_ingreso} día(s)` : 'N/A'}
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
