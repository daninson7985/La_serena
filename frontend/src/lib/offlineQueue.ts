import { api, Actividad } from './api';

const STORAGE_KEY = 'matriz_sgr_offline_queue';

export interface OfflineRegistro {
  id_local: string;
  fecha_creacion: string;
  data: Partial<Actividad> & { url_foto_simulada?: string };
}

export const offlineQueue = {
  guardar(data: Partial<Actividad> & { url_foto_simulada?: string }): OfflineRegistro {
    const queue = this.listar();
    const nuevo: OfflineRegistro = {
      id_local: `off-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      fecha_creacion: new Date().toISOString(),
      data,
    };
    queue.push(nuevo);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
    }
    return nuevo;
  },

  listar(): OfflineRegistro[] {
    if (typeof window === 'undefined') return [];
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  },

  eliminar(id_local: string): void {
    if (typeof window === 'undefined') return;
    const items = this.listar().filter(i => i.id_local !== id_local);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  },

  async sincronizar(): Promise<{ total: number; exitosos: number; fallidos: number }> {
    const queue = this.listar();
    if (queue.length === 0) return { total: 0, exitosos: 0, fallidos: 0 };

    let exitosos = 0;
    let fallidos = 0;

    for (const item of queue) {
      try {
        await api.crearActividad(item.data);
        this.eliminar(item.id_local);
        exitosos++;
      } catch (err) {
        console.error('Error sincronizando item offline:', err);
        fallidos++;
      }
    }

    return { total: queue.length, exitosos, fallidos };
  },
};
