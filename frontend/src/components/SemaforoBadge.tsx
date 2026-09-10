import React from 'react';

interface SemaforoBadgeProps {
  color: 'VERDE' | 'AMBAR' | 'ROJO' | string;
  porcentaje?: number;
  tamano?: 'sm' | 'md' | 'lg';
  mostrarTexto?: boolean;
}

export const SemaforoBadge: React.FC<SemaforoBadgeProps> = ({
  color,
  porcentaje,
  tamano = 'md',
  mostrarTexto = true,
}) => {
  const configs = {
    VERDE: {
      bg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
      dot: 'bg-emerald-500',
      label: 'Óptimo (Meta Cumplida)',
      icon: '🟢',
    },
    AMBAR: {
      bg: 'bg-amber-100 text-amber-800 border-amber-300',
      dot: 'bg-amber-500',
      label: 'Alerta (60% - 99%)',
      icon: '🟡',
    },
    ROJO: {
      bg: 'bg-rose-100 text-rose-800 border-rose-300',
      dot: 'bg-rose-500',
      label: 'Crítico (< 60%)',
      icon: '🔴',
    },
  };

  const key = (color in configs ? color : 'ROJO') as keyof typeof configs;
  const config = configs[key];

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3.5 py-1.5 font-bold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${config.bg} ${sizeStyles[tamano]}`}
    >
      <span className={`h-2 w-2 rounded-full ${config.dot} animate-pulse`} />
      <span>{config.icon}</span>
      {mostrarTexto && <span>{config.label}</span>}
      {porcentaje !== undefined && (
        <span className="ml-1 font-semibold">({porcentaje}%)</span>
      )}
    </span>
  );
};
