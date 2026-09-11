import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  LayoutDashboard,
  UserCheck,
  ClipboardList,
  CheckCircle2,
  Smartphone,
  Users,
  ShieldCheck,
  LogOut,
  Wifi,
  WifiOff,
  RefreshCw
} from 'lucide-react';
import { Usuario } from '../lib/api';
import { offlineQueue } from '../lib/offlineQueue';

export const Navbar: React.FC = () => {
  const router = useRouter();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [offlineCount, setOfflineCount] = useState<number>(0);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  useEffect(() => {
    // Cargar usuario de localStorage
    const stored = localStorage.getItem('matriz_sgr_user');
    if (stored) {
      try {
        setUsuario(JSON.parse(stored));
      } catch (e) {
        console.error(e);
      }
    }

    // Comprobar estado de conexión
    setIsOnline(navigator.onLine);
    const updateOnline = () => setIsOnline(true);
    const updateOffline = () => setIsOnline(false);
    window.addEventListener('online', updateOnline);
    window.addEventListener('offline', updateOffline);

    // Revisar cola offline
    setOfflineCount(offlineQueue.listar().length);
    const interval = setInterval(() => {
      setOfflineCount(offlineQueue.listar().length);
    }, 3000);

    return () => {
      window.removeEventListener('online', updateOnline);
      window.removeEventListener('offline', updateOffline);
      clearInterval(interval);
    };
  }, []);

  const handleSincronizar = async () => {
    setIsSyncing(true);
    const res = await offlineQueue.sincronizar();
    setIsSyncing(false);
    setOfflineCount(offlineQueue.listar().length);
    alert(`Sincronización completada: ${res.exitosos} actividades enviadas con éxito.`);
  };

  const handleLogout = () => {
    localStorage.removeItem('matriz_sgr_user');
    localStorage.removeItem('matriz_sgr_token');
    router.push('/');
  };

  const navItems = [
    { label: 'Dashboard General', href: '/dashboard', icon: LayoutDashboard },
    { label: 'Dashboard Personal', href: '/personal', icon: UserCheck },
    { label: 'Tubo de Trabajo', href: '/tubo', icon: ClipboardList },
    { label: 'Validación "Check"', href: '/verificacion', icon: CheckCircle2 },
    { label: 'Terreno (3 Clics)', href: '/terreno', icon: Smartphone },
    { label: 'Casos Sociales', href: '/casos-sociales', icon: Users },
    { label: 'Auditoría', href: '/auditoria', icon: ShieldCheck },
  ];

  return (
    <header className="bg-slate-900 text-white shadow-md sticky top-0 z-50">
      {/* Top Bar Institucional */}
      <div className="bg-slate-950 px-4 py-1.5 border-b border-slate-800 text-xs text-slate-300 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="font-bold text-red-500">MUNICIPALIDAD DE LA SERENA</span>
          <span className="text-slate-500">|</span>
          <span>Sistema de Gestión de Resultados (Matriz SGR)</span>
          <span className="text-slate-500">|</span>
          <span className="text-amber-400 font-medium">Trimestre 3 - 2026</span>
        </div>

        {/* Estado Conexión & Sincronización */}
        <div className="flex items-center gap-3">
          {isOnline ? (
            <span className="inline-flex items-center gap-1 text-emerald-400">
              <Wifi size={13} /> Conectado
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-rose-400 animate-pulse font-bold">
              <WifiOff size={13} /> Modo Offline
            </span>
          )}

          {offlineCount > 0 && (
            <button
              onClick={handleSincronizar}
              disabled={!isOnline || isSyncing}
              className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-2 py-0.5 rounded flex items-center gap-1 disabled:opacity-50 transition-colors"
            >
              <RefreshCw size={12} className={isSyncing ? 'animate-spin' : ''} />
              <span>Sincronizar ({offlineCount})</span>
            </button>
          )}

          {usuario && (
            <div className="flex items-center gap-2 pl-3 border-l border-slate-800">
              <span className="bg-blue-900/60 text-blue-300 px-2 py-0.5 rounded text-[11px] font-semibold">
                {usuario.rol}
              </span>
              <span className="text-slate-200 font-medium">{usuario.first_name} {usuario.last_name}</span>
              {usuario.delegacion_codigo && (
                <span className="text-slate-400 text-[11px]">({usuario.delegacion_codigo})</span>
              )}
              <button
                onClick={handleLogout}
                title="Cerrar sesión"
                className="text-slate-400 hover:text-rose-400 ml-1 p-0.5"
              >
                <LogOut size={13} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Nav Navigation */}
      <nav className="max-w-7xl mx-auto px-4 py-2.5 flex items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-gradient-to-tr from-red-600 to-amber-500 flex items-center justify-center font-black text-white text-base shadow">
            LS
          </div>
          <div>
            <div className="font-extrabold tracking-tight text-white leading-none text-base">
              MATRIZ <span className="text-red-500">SGR</span>
            </div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Gestión Territorial</div>
          </div>
        </Link>

        {/* Links */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = router.pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-red-600 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon size={15} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
};
