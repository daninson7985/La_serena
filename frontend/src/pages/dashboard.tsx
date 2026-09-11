import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import {
  Building2,
  Users,
  AlertTriangle,
  Clock,
  CheckCircle2,
  TrendingUp,
  Filter,
  Eye,
  RefreshCw
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { SemaforoBadge } from '../components/SemaforoBadge';
import { api, ResumenComunal, ResumenDelegacion, Usuario } from '../lib/api';

export default function DashboardPage() {
  const [comunalData, setComunalData] = useState<ResumenComunal | null>(null);
  const [delegaciones, setDelegaciones] = useState<any[]>([]);
  const [delegacionFiltro, setDelegacionFiltro] = useState<string>('todas');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<Usuario | null>(null);

  const cargarDatos = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMetricasComunal();
      setComunalData(data);
      const dels = await api.getDelegaciones();
      setDelegaciones(dels);
    } catch (err: any) {
      setError(err.message || 'Error cargando indicadores.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const userStr = localStorage.getItem('matriz_sgr_user');
    if (userStr) {
      try {
        const u = JSON.parse(userStr);
        setCurrentUser(u);
        if (u.rol === 'DELEGADO' && u.delegacion) {
          setDelegacionFiltro(u.delegacion.toString());
        }
      } catch (e) {
        console.error(e);
      }
    }
    cargarDatos();
  }, []);

  // Filtrado de delegaciones
  const delegacionesFiltradas = comunalData?.delegaciones.filter((d) => {
    if (delegacionFiltro === 'todas') return true;
    return d.delegacion_id.toString() === delegacionFiltro;
  }) || [];

  // Calcular totales filtrados
  const totalFuncionarios = delegacionesFiltradas.reduce((acc, d) => acc + d.total_funcionarios, 0);
  const promedioPonderado = delegacionesFiltradas.length > 0
    ? (delegacionesFiltradas.reduce((acc, d) => acc + d.promedio_ponderado_pct, 0) / delegacionesFiltradas.length).toFixed(1)
    : '0.0';

  const totalPendientesCheck = delegacionesFiltradas.reduce((acc, d) => acc + d.evidencias_pendientes_check, 0);
  const totalVencidos = delegacionesFiltradas.reduce((acc, d) => acc + d.compromisos.vencidos, 0);

  const todosLosFuncionarios = delegacionesFiltradas.flatMap((d) => d.funcionarios);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Head>
        <title>Dashboard General | Matriz SGR La Serena</title>
      </Head>

      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-6">
        {/* Cabecera y Filtros */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 p-5 rounded-2xl border border-slate-800 shadow-lg">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-red-600/20 text-red-400 border border-red-500/30 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider">
                Panel de Coordinación y Delegaciones
              </span>
              {comunalData && (
                <span className="text-xs text-slate-400 font-mono">
                  Período: {comunalData.periodo_nombre}
                </span>
              )}
            </div>
            <h1 className="text-2xl font-black text-white mt-1">
              Dashboard General de Gestión Territorial
            </h1>
            <p className="text-xs text-slate-400">
              Monitoreo transversal de cumplimiento, avance del semáforo y alertas operativas comunales.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2">
              <Filter size={15} className="text-slate-400" />
              <label className="text-xs font-bold text-slate-400 uppercase">Delegación:</label>
              <select
                value={delegacionFiltro}
                onChange={(e) => setDelegacionFiltro(e.target.value)}
                className="bg-transparent text-sm font-semibold text-white focus:outline-none cursor-pointer"
              >
                <option value="todas" className="bg-slate-900">Todas las Delegaciones (6)</option>
                {delegaciones.map((d) => (
                  <option key={d.id} value={d.id.toString()} className="bg-slate-900">
                    {d.nombre} ({d.codigo})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={cargarDatos}
              disabled={loading}
              className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700 transition-colors"
              title="Refrescar indicadores"
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-4 rounded-xl text-sm flex items-center gap-3">
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* Tarjetas de Indicadores Clave (KPIs) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Promedio Ponderado */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl relative overflow-hidden">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Cumplimiento Promedio
              </span>
              <div className="p-2 bg-blue-500/10 text-blue-400 rounded-xl">
                <TrendingUp size={18} />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-white">{promedioPonderado}%</span>
              <span className="text-xs text-slate-400">meta al día: {comunalData?.meta_esperada_pct}%</span>
            </div>
            <div className="mt-2">
              {comunalData && (
                <SemaforoBadge
                  color={comunalData.semaforo_comunal}
                  tamano="sm"
                  mostrarTexto={true}
                />
              )}
            </div>
          </div>

          {/* Evidencias por Validar (Check del Delegado) */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl relative overflow-hidden">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Evidencias Pendientes
              </span>
              <div className="p-2 bg-amber-500/10 text-amber-400 rounded-xl">
                <CheckCircle2 size={18} />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-amber-400">{totalPendientesCheck}</span>
              <span className="text-xs text-slate-400">fotos por validar</span>
            </div>
            <div className="mt-2">
              <Link
                href="/verificacion"
                className="text-xs font-semibold text-amber-400 hover:text-amber-300 underline inline-flex items-center gap-1"
              >
                Ir a Validación "Check" &rarr;
              </Link>
            </div>
          </div>

          {/* Tubo de Trabajo: Compromisos Vencidos */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl relative overflow-hidden">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Compromisos Vencidos
              </span>
              <div className="p-2 bg-rose-500/10 text-rose-400 rounded-xl">
                <Clock size={18} />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-rose-400">{totalVencidos}</span>
              <span className="text-xs text-slate-400">en Tubo de Trabajo</span>
            </div>
            <div className="mt-2">
              <Link
                href="/tubo"
                className="text-xs font-semibold text-rose-400 hover:text-rose-300 underline inline-flex items-center gap-1"
              >
                Revisar Agenda Colectiva &rarr;
              </Link>
            </div>
          </div>

          {/* Dotación y Cobertura */}
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl relative overflow-hidden">
            <div className="flex justify-between items-start">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Funcionarios Activos
              </span>
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl">
                <Users size={18} />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-white">{totalFuncionarios}</span>
              <span className="text-xs text-slate-400">en {delegacionesFiltradas.length} delegaciones</span>
            </div>
            <div className="mt-2 text-xs text-emerald-400 font-semibold">
              100% registros anonimizados
            </div>
          </div>
        </div>

        {/* Resumen por Delegaciones (Cards / Grid) */}
        {delegacionFiltro === 'todas' && (
          <div className="space-y-3">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Building2 size={20} className="text-red-500" />
              Estado Comparativo por Delegaciones Territoriales
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {comunalData?.delegaciones.map((del) => (
                <div
                  key={del.delegacion_id}
                  className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all space-y-4"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[11px] font-mono text-slate-400 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                        {del.codigo}
                      </span>
                      <h3 className="text-base font-extrabold text-white mt-1">{del.nombre}</h3>
                    </div>
                    <SemaforoBadge color={del.semaforo_delegacion} tamano="sm" />
                  </div>

                  <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-xs">
                    <div className="flex justify-between text-slate-400">
                      <span>Cumplimiento Ponderado:</span>
                      <span className="font-bold text-white">{del.promedio_ponderado_pct}%</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Funcionarios Medidos:</span>
                      <span className="font-bold text-white">{del.total_funcionarios}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Evidencias Pendientes Check:</span>
                      <span className={`font-bold ${del.evidencias_pendientes_check > 0 ? 'text-amber-400' : 'text-slate-300'}`}>
                        {del.evidencias_pendientes_check}
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Compromisos Vencidos:</span>
                      <span className={`font-bold ${del.compromisos.vencidos > 0 ? 'text-rose-400' : 'text-slate-300'}`}>
                        {del.compromisos.vencidos}
                      </span>
                    </div>
                  </div>

                  {/* Distribución Semáforo */}
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-500 font-medium">Semáforos:</span>
                    <div className="flex items-center gap-2">
                      <span className="text-emerald-400 font-bold">🟢 {del.distribucion_semaforo.verde}</span>
                      <span className="text-amber-400 font-bold">🟡 {del.distribucion_semaforo.ambar}</span>
                      <span className="text-rose-400 font-bold">🔴 {del.distribucion_semaforo.rojo}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tabla Detallada de Funcionarios */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-5 border-b border-slate-800 flex justify-between items-center">
            <div>
              <h3 className="text-base font-bold text-white">
                Fichas y Desempeño de Funcionarios de Terreno
              </h3>
              <p className="text-xs text-slate-400">
                Monitoreo individual de avance de metas diarias y semáforos.
              </p>
            </div>
            <span className="text-xs bg-slate-800 text-slate-300 px-3 py-1 rounded-full font-mono">
              {todosLosFuncionarios.length} funcionarios listados
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3.5">Funcionario</th>
                  <th className="p-3.5">Cargo</th>
                  <th className="p-3.5">Delegación</th>
                  <th className="p-3.5 text-center">Cumplimiento Ponderado</th>
                  <th className="p-3.5 text-center">Semáforo</th>
                  <th className="p-3.5 text-center">Actividad Reciente</th>
                  <th className="p-3.5 text-center">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {todosLosFuncionarios.map((f) => (
                  <tr key={f.funcionario_id} className="hover:bg-slate-850/50 transition-colors">
                    <td className="p-3.5 font-bold text-white">
                      <div>{f.nombre_completo}</div>
                      <div className="text-[10px] text-slate-400 font-mono font-normal">{f.username}</div>
                    </td>
                    <td className="p-3.5 text-slate-300">{f.cargo}</td>
                    <td className="p-3.5">
                      <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono text-[11px]">
                        {f.delegacion_codigo}
                      </span>
                    </td>
                    <td className="p-3.5 text-center font-bold text-base text-white">
                      {f.total_ponderado_pct}%
                    </td>
                    <td className="p-3.5 text-center">
                      <SemaforoBadge color={f.semaforo_global} tamano="sm" />
                    </td>
                    <td className="p-3.5 text-center text-slate-400">
                      {f.dias_sin_ingreso !== null ? (
                        f.dias_sin_ingreso === 0 ? (
                          <span className="text-emerald-400 font-semibold">Hoy</span>
                        ) : (
                          <span className={f.dias_sin_ingreso > 3 ? 'text-amber-400 font-bold' : ''}>
                            Hace {f.dias_sin_ingreso} día(s)
                          </span>
                        )
                      ) : (
                        <span className="text-slate-600">Sin registros</span>
                      )}
                    </td>
                    <td className="p-3.5 text-center">
                      <Link
                        href={`/personal?id=${f.funcionario_id}`}
                        className="inline-flex items-center gap-1 bg-red-600/20 hover:bg-red-600 text-red-300 hover:text-white px-2.5 py-1.5 rounded-lg border border-red-500/30 transition-all font-semibold text-xs"
                      >
                        <Eye size={13} />
                        <span>Ver Ficha</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
