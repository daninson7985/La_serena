import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { Shield, KeyRound, User, Lock, ArrowRight, CheckCircle, AlertTriangle } from 'lucide-react';
import { api } from '../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Estados para el módulo 2FA de Rodrigo
  const [show2FA, setShow2FA] = useState(false);
  const [userId2FA, setUserId2FA] = useState<number | null>(null);
  const [twoFactorCode, setTwoFactorCode] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await api.login({ username, password });
      if (res.requires_2fa) {
        setShow2FA(true);
        setUserId2FA(res.user_id || null);
      } else if (res.user && res.token) {
        localStorage.setItem('matriz_sgr_user', JSON.stringify(res.user));
        localStorage.setItem('matriz_sgr_token', res.token);
        // Redirigir según rol
        if (res.user.rol === 'FUNCIONARIO') {
          router.push('/personal');
        } else {
          router.push('/dashboard');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión. Verifique sus credenciales.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId2FA) return;
    setLoading(true);
    setError(null);

    try {
      const res = await api.verificar2FA({ user_id: userId2FA, code: twoFactorCode });
      if (res.success && res.user) {
        localStorage.setItem('matriz_sgr_user', JSON.stringify(res.user));
        localStorage.setItem('matriz_sgr_token', res.token);
        router.push('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Código 2FA incorrecto.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-850 to-red-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Cabecera Institucional */}
        <div className="bg-gradient-to-r from-red-700 to-red-600 p-6 text-white text-center relative">
          <div className="inline-flex p-2 bg-white rounded-2xl mb-3 shadow-md w-20 h-20 items-center justify-center overflow-hidden">
            <img src="/logo_la_serena.png" alt="Logo Municipalidad de La Serena" className="w-full h-full object-contain" />
          </div>
          <h1 className="text-xl font-black uppercase tracking-tight">Municipalidad de La Serena</h1>
          <p className="text-xs font-semibold text-red-100 mt-1 uppercase tracking-widest">
            Sistema de Gestión de Resultados (Matriz SGR)
          </p>
          <div className="mt-2 inline-block bg-black/20 text-[11px] px-2.5 py-0.5 rounded-full text-amber-200">
            Control Territorial & Desempeño
          </div>
        </div>

        {/* Cuerpo del Formulario */}
        <div className="p-6">
          {error && (
            <div className="mb-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 p-3 rounded-xl text-xs flex items-center gap-2">
              <AlertTriangle size={16} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!show2FA ? (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1 uppercase tracking-wider">
                  Usuario Institucional
                </label>
                <div className="relative">
                  <User size={16} className="absolute left-3.5 top-3.5 text-slate-500" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-10 pr-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                    placeholder="ej. pablo.cuadra"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1 uppercase tracking-wider">
                  Contraseña Segura
                </label>
                <div className="relative">
                  <Lock size={16} className="absolute left-3.5 top-3.5 text-slate-500" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-10 pr-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
                    placeholder="••••••••••••"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-red-900/40 transition-all disabled:opacity-50"
              >
                {loading ? 'Validando...' : 'Iniciar Sesión'}
                <ArrowRight size={16} />
              </button>
            </form>
          ) : (
            /* Pantalla 2FA preparada para Rodrigo */
            <form onSubmit={handleVerify2FA} className="space-y-4">
              <div className="text-center p-3 bg-blue-950/40 border border-blue-800/40 rounded-xl mb-4">
                <KeyRound size={28} className="mx-auto text-blue-400 mb-2" />
                <h3 className="text-sm font-bold text-white">Autenticación de Dos Factores (2FA)</h3>
                <p className="text-xs text-slate-400 mt-1">
                  Ingrese el código numérico de 6 dígitos (código de prueba: <strong>123456</strong>)
                </p>
              </div>

              <div>
                <input
                  type="text"
                  maxLength={6}
                  value={twoFactorCode}
                  onChange={(e) => setTwoFactorCode(e.target.value)}
                  required
                  autoFocus
                  className="w-full bg-slate-950 border border-blue-600 rounded-xl py-3 text-center text-xl font-mono tracking-widest text-white focus:outline-none"
                  placeholder="000000"
                />
              </div>

              <button
                type="submit"
                disabled={loading || twoFactorCode.length < 6}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-50"
              >
                {loading ? 'Verificando...' : 'Confirmar Código 2FA'}
                <CheckCircle size={16} />
              </button>
            </form>
          )}


        </div>
      </div>
    </div>
  );
}
