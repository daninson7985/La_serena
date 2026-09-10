# Frontend - Matriz SGR (Sistema de Gestión de Resultados)
### Ilustre Municipalidad de La Serena | Proyecto Integrador INACAP

Frontend moderno e interactivo desarrollado en **Next.js 14** (React 18), **TypeScript** y **Tailwind CSS**. Proporciona una interfaz visual responsiva, accesible tanto desde computadores de escritorio en delegaciones como desde dispositivos móviles en terreno por funcionarios municipales.

---

## 1. Arquitectura y Estructura del Módulo

```text
frontend/
├── package.json                  # Dependencias del proyecto (Next.js, React, Tailwind, Lucide)
├── tsconfig.json                 # Configuración de TypeScript
├── tailwind.config.ts            # Configuración de estilos Tailwind y paleta institucional
├── next.config.mjs               # Configuración de Next.js (headers, proxy, imágenes)
├── public/                       # Activos estáticos, logos institucionales e iconos
└── src/
    ├── components/               # Componentes React reutilizables
    │   ├── Navbar.tsx            # Barra de navegación con perfil de usuario y logout
    │   └── SemaforoBadge.tsx     # Indicador visual dinámico (Verde, Ámbar, Rojo)
    ├── lib/                      # Capa de servicios y comunicación
    │   ├── api.ts                # Cliente API REST con tipado TypeScript completo
    │   └── offlineQueue.ts       # Cola de sincronización local para trabajo sin conexión
    ├── pages/                    # Enrutamiento basado en páginas (Pages Router)
    │   ├── index.tsx             # Login de usuario con soporte para 2FA
    │   ├── dashboard.tsx         # Tablero principal de métricas comunales y por delegación
    │   ├── tubo.tsx              # Tubo de trabajo (compromisos ciudadanos y solicitudes)
    │   ├── verificacion.tsx      # Bandeja de revisión y aprobación de evidencias fotográficas
    │   └── personal.tsx          # Vista individual del funcionario y cumplimiento de metas
    └── styles/
        └── globals.css           # Estilos globales y utilidades personalizadas
```

---

## 2. Requisitos Previos e Instalación

### Requisitos:
* Node.js 18.x o superior (recomendado LTS Node.js 20.x).
* Gestor de paquetes `npm` (o `yarn` / `pnpm`).

### Paso 1: Instalar dependencias
Desde la carpeta raíz del proyecto o desde `frontend/`:

```bash
cd frontend
npm install
```

### Paso 2: Configurar variable de entorno (Opcional)
Por defecto, el frontend se comunica con el backend local en `http://127.0.0.1:8000/api`. Si deseas personalizar la URL de la API, crea un archivo `.env.local` en `frontend/`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
```

### Paso 3: Iniciar el servidor de desarrollo
```bash
npm run dev
```
La aplicación estará disponible en `http://localhost:3000/`.

---

## 3. Catálogo de Pantallas y Funcionalidades

| Ruta | Pantalla | Rol / Acceso | Funcionalidad Clave |
| :--- | :--- | :--- | :--- |
| `/` | **Inicio de Sesión** | Público | Autenticación con usuario/contraseña y verificación 2FA. |
| `/dashboard` | **Panel Comunal** | Admin / Coordinador | Visión global de las 6 delegaciones, ranking de cumplimiento y semáforo general. |
| `/tubo` | **Tubo de Trabajo** | Delegado / Funcionario | Gestión de compromisos vecinales en estados: Ingresado, Pendiente, En Proceso, Realizado. Alerta roja en vencidos. |
| `/verificacion` | **Bandeja de Evidencias**| Delegado / Verificador | Aprobación/Rechazo de fotografías en terreno con validación de código verificador inmutable. |
| `/personal` | **Mi Desempeño** | Funcionario | Vista individual de metas trimestrales, avance porcentual, tope del 150% e historial de actividades. |

---

## 4. Características de Resiliencia y Terreno

* **Trabajo en Terreno y Modo Sin Conexión (`offlineQueue.ts`):** Permite registrar actividades en zonas con baja conectividad móvil (ej. sectores rurales de La Serena). Las solicitudes se encolan en `localStorage` y se sincronizan automáticamente con el backend al recuperar señal.
* **Componente `SemaforoBadge`:** Renderiza visualmente el estado del funcionario según los umbrales de la regla de negocio $RN	ext{-}008$:
  * `VERDE`: Avance >= 100% de la meta esperada al día.
  * `AMBAR`: Avance entre 60% y 99%.
  * `ROJO`: Avance < 60% (retraso crítico).
* **Diseño Responsivo:** Adaptado para teléfonos inteligentes utilizados en rondas de inspección y pantallas de escritorio en oficinas municipales.

---

## 5. Scripts Disponibles

* `npm run dev`: Inicia el servidor de desarrollo con recarga en caliente (Hot Reload).
* `npm run build`: Compila la aplicación optimizada para producción.
* `npm run start`: Inicia el servidor optimizado de producción.
* `npm run lint`: Ejecuta el análisis estático de código ESLint.
