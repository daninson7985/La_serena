export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export interface Usuario {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  rol: 'ADMIN' | 'COORDINADOR' | 'DELEGADO' | 'FUNCIONARIO';
  cargo: number | null;
  cargo_nombre?: string;
  delegacion: number | null;
  delegacion_nombre?: string;
  delegacion_codigo?: string;
  telefono?: string;
  rut_anonimizado?: string;
  requires_2fa: boolean;
}

export interface ItemMedicion {
  id: number;
  nombre_item: string;
  descripcion?: string;
  meta_cuantitativa: number;
  ponderador: number;
  unidad_medida: string;
  cargo: number;
  periodo: number;
}

export interface Evidencia {
  id: number;
  actividad: number;
  codigo_verificador: string;
  archivo_foto?: string;
  url_foto_simulada?: string;
  hash_sha256?: string;
  estado: 'PENDIENTE' | 'APROBADA' | 'RECHAZADA' | 'CORRECCION';
  verificador?: number;
  verificador_nombre?: string;
  fecha_validacion?: string;
  observacion?: string;
  fecha_subida: string;
}

export interface Actividad {
  id: number;
  fecha_registro: string;
  fecha_actividad: string;
  funcionario: number;
  funcionario_nombre?: string;
  delegacion: number;
  delegacion_nombre?: string;
  delegacion_codigo?: string;
  item_medicion?: number;
  item_nombre?: string;
  catalogo_servicio?: number;
  actividad_solicitud: string;
  accion_ejecutada: string;
  contacto_nombre?: string;
  contacto_telefono?: string;
  latitud?: number;
  longitud?: number;
  evidencia?: Evidencia;
}

export interface Compromiso {
  id: number;
  solicitante: string;
  delegacion: number;
  delegacion_nombre?: string;
  delegacion_codigo?: string;
  responsable: number;
  responsable_nombre?: string;
  fecha_registro: string;
  fecha_comprometida: string;
  area_apoyo?: string;
  descripcion: string;
  estado: 'INGRESADO' | 'PENDIENTE' | 'EN_PROCESO' | 'REALIZADO';
  observaciones?: string;
}

export interface MetricaItem {
  item_id: number;
  nombre: string;
  descripcion?: string;
  meta: number;
  unidad: string;
  ponderador: number;
  avance_aprobado: number;
  evidencias_pendientes: number;
  evidencias_rechazadas: number;
  cumplimiento_pct: number;
  aporte_ponderado: number;
  semaforo: 'VERDE' | 'AMBAR' | 'ROJO';
}

export interface MetricasFuncionario {
  funcionario_id: number;
  nombre_completo: string;
  username: string;
  cargo: string;
  delegacion: string;
  delegacion_codigo: string;
  periodo_nombre: string;
  meta_esperada_pct: number;
  dias_transcurridos: number;
  dias_totales: number;
  total_ponderado_pct: number;
  semaforo_global: 'VERDE' | 'AMBAR' | 'ROJO';
  items: MetricaItem[];
  ultima_actividad?: string;
  dias_sin_ingreso?: number;
  total_actividades: number;
  promedio_diario: number;
  compromisos: {
    total: number;
    realizados: number;
    pendientes: number;
    porcentaje_realizado: number;
  };
}

export interface ResumenDelegacion {
  delegacion_id: number;
  nombre: string;
  codigo: string;
  periodo_nombre: string;
  meta_esperada_pct: number;
  promedio_ponderado_pct: number;
  semaforo_delegacion: 'VERDE' | 'AMBAR' | 'ROJO';
  total_funcionarios: number;
  distribucion_semaforo: {
    verde: number;
    ambar: number;
    rojo: number;
  };
  compromisos: {
    total: number;
    realizados: number;
    pendientes: number;
    vencidos: number;
  };
  evidencias_pendientes_check: number;
  funcionarios: MetricasFuncionario[];
}

export interface ResumenComunal {
  periodo_nombre: string;
  meta_esperada_pct: number;
  promedio_comunal_pct: number;
  semaforo_comunal: 'VERDE' | 'AMBAR' | 'ROJO';
  total_evidencias_pendientes: number;
  total_compromisos_vencidos: number;
  delegaciones: ResumenDelegacion[];
}

// Helper fetch wrapper
async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.error || `Error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Auth
  login: (credentials: { username: string; password: string }) =>
    apiFetch<{ requires_2fa: boolean; user?: Usuario; token?: string; user_id?: number; message?: string }>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  verificar2FA: (data: { user_id: number; code: string }) =>
    apiFetch<{ success: boolean; user: Usuario; token: string }>('/auth/verificar-2fa/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Delegaciones & Usuarios
  getDelegaciones: () => apiFetch<any[]>('/delegaciones/'),
  getUsuarios: (params?: { delegacion?: number; rol?: string }) => {
    const q = new URLSearchParams();
    if (params?.delegacion) q.set('delegacion', params.delegacion.toString());
    if (params?.rol) q.set('rol', params.rol);
    return apiFetch<Usuario[]>(`/usuarios/?${q.toString()}`);
  },

  // Catálogos & Ítems
  getCatalogos: () => apiFetch<any[]>('/catalogos/'),
  getItemsMedicion: (params?: { cargo?: number; periodo?: number }) => {
    const q = new URLSearchParams();
    if (params?.cargo) q.set('cargo', params.cargo.toString());
    if (params?.periodo) q.set('periodo', params.periodo.toString());
    return apiFetch<ItemMedicion[]>(`/items-medicion/?${q.toString()}`);
  },

  // Actividades
  getActividades: (params?: { delegacion?: number; funcionario?: number }) => {
    const q = new URLSearchParams();
    if (params?.delegacion) q.set('delegacion', params.delegacion.toString());
    if (params?.funcionario) q.set('funcionario', params.funcionario.toString());
    return apiFetch<Actividad[]>(`/actividades/?${q.toString()}`);
  },

  crearActividad: (data: Partial<Actividad> & { url_foto_simulada?: string }) =>
    apiFetch<Actividad>('/actividades/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Evidencias & Check
  getEvidencias: (params?: { delegacion?: number; estado?: string }) => {
    const q = new URLSearchParams();
    if (params?.delegacion) q.set('delegacion', params.delegacion.toString());
    if (params?.estado) q.set('estado', params.estado);
    return apiFetch<Evidencia[]>(`/evidencias/?${q.toString()}`);
  },

  validarEvidencia: (id: number, data: { decision: 'APROBADA' | 'RECHAZADA' | 'CORRECCION'; observacion?: string; verificador?: number }) =>
    apiFetch<Evidencia>(`/evidencias/${id}/validar/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Tubo de Trabajo (Compromisos)
  getCompromisos: (params?: { delegacion?: number; responsable?: number; estado?: string }) => {
    const q = new URLSearchParams();
    if (params?.delegacion) q.set('delegacion', params.delegacion.toString());
    if (params?.responsable) q.set('responsable', params.responsable.toString());
    if (params?.estado) q.set('estado', params.estado);
    return apiFetch<Compromiso[]>(`/compromisos/?${q.toString()}`);
  },

  cambiarEstadoCompromiso: (id: number, data: { estado: string; observacion?: string }) =>
    apiFetch<Compromiso>(`/compromisos/${id}/cambiar-estado/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Métricas
  getMetricasComunal: () => apiFetch<ResumenComunal>('/metricas/?tipo=comunal'),
  getMetricasDelegacion: (delegacionId: number) => apiFetch<ResumenDelegacion>(`/metricas/?tipo=delegacion&delegacion_id=${delegacionId}`),
  getMetricasFuncionario: (funcionarioId: number) => apiFetch<MetricasFuncionario>(`/metricas/?tipo=funcionario&funcionario_id=${funcionarioId}`),

  // Casos Sociales
  getCasosSociales: () => apiFetch<any[]>('/casos-sociales/'),

  // Auditoría
  getAuditoria: () => apiFetch<any[]>('/auditoria/'),
};
