# Backend - Matriz SGR (Sistema de Gestión de Resultados)
### Ilustre Municipalidad de La Serena | Proyecto Integrador INACAP

Backend robusto desarrollado en **Python 3.12** y **Django 6.1.1** con arquitectura de API REST utilizando **Django REST Framework (DRF)**. Implementa la lógica de negocio municipal, cálculo del semáforo ponderado, control de acceso basado en roles (RBAC) y doble modalidad de consumo (API REST y vistas web renderizadas con Bootstrap 5).

---

## 1. Arquitectura y Estructura del Módulo

```text
backend/
├── manage.py                     # CLI de administración de Django
├── db.sqlite3                    # Base de datos relacional (desarrollo)
├── sgr_backend/                  # Configuración principal del proyecto
│   ├── settings.py               # Variables, apps instaladas, CORS, auth
│   ├── urls.py                   # Enrutamiento maestro (Admin, Web views, API)
│   ├── wsgi.py                   # Entrypoint WSGI para despliegue
│   └── asgi.py                   # Entrypoint ASGI asíncrono
├── sgr_app/                      # Núcleo de la aplicación Matriz SGR
│   ├── models.py                 # 12 modelos relacionales en 3NF
│   ├── serializers.py            # Serializadores REST con validación
│   ├── views.py                  # API ViewSets y endpoints REST
│   ├── web_views.py              # Controladores para vistas web
│   ├── urls.py                   # Enrutador de la API (/api/...)
│   ├── tests.py                  # Suite de pruebas unitarias automatizadas
│   ├── services/
│   │   └── calculos.py           # Motor matemático del semáforo y cumplimiento
│   └── management/commands/
│       └── poblar_sgr.py         # Seeder con datos reales de las 6 delegaciones
├── templates/                    # Plantillas HTML con Bootstrap 5
└── static/                       # Archivos estáticos (CSS, JS, iconos)
```

---

## 2. Requisitos Previos e Instalación

### Requisitos:
* Python 3.10 o superior (recomendado Python 3.12).
* Entorno virtual `venv`.

### Paso 1: Crear y activar el entorno virtual
Desde la carpeta raíz del proyecto o desde `backend/`:

```powershell
# En Windows (PowerShell):
cd backend
python -m venv venv
venv\Scripts\activate
```

### Paso 2: Instalar dependencias
```powershell
pip install -r ../requirements.txt
```

### Paso 3: Ejecutar migraciones
Aplica las 12 tablas en la base de datos relacional:
```powershell
python manage.py migrate
```

### Paso 4: Cargar datos iniciales (Seeder)
Genera automáticamente las 6 delegaciones oficiales de La Serena, cargos, período Q1-2026, catálogo de servicios, ítems de medición ponderados y usuarios de prueba:
```powershell
python manage.py poblar_sgr
```

### Paso 5: Iniciar el servidor de desarrollo
```powershell
python manage.py runserver
```
El servidor estará escuchando en `http://127.0.0.1:8000/`.

---

## 3. Cuentas de Usuario de Prueba Precargadas

| Usuario | Contraseña | Rol | Asignación / Territorio |
| :--- | :--- | :--- | :--- |
| `admin` | `AdminSGR2026!` | `ADMIN` | Administrador Comunal (Acceso total) |
| `coordinador` | `CoordSGR2026!` | `COORDINADOR` | Coordinador Comunal de Delegaciones |
| `delegado_centro` | `Delegado2026!` | `DELEGADO` | Delegación Municipal La Serena Centro |
| `funcionario_centro` | `Func2026!` | `FUNCIONARIO` | Funcionario en Terreno (Centro) |

---

## 4. Catálogo de la API REST (`/api/`)

Todos los endpoints devuelven respuestas en formato JSON estructurado y admiten filtros por delegación, período y funcionario.

### A. Autenticación y Seguridad
* `POST /api/auth/login/`
  * **Payload:** `{"username": "...", "password": "..."}`
  * **Respuesta:** Token/sesión, datos del usuario, rol y flag `requires_2fa`.
* `POST /api/auth/verificar-2fa/`
  * **Payload:** `{"user_id": X, "token": "123456"}`
  * **Respuesta:** Validación de token TOTP de 6 dígitos.

### B. Motor de Métricas y Semáforo (Cálculo Dinámico)
* `GET /api/metricas/?funcionario_id=X&periodo_id=Y`
  * Calcula en tiempo real:
    * Días transcurridos vs días totales del período.
    * % Meta acumulada esperada al día (RN-007).
    * Cumplimiento por ítem con tope de 150% (RN-005).
    * Cumplimiento ponderado general (RN-001).
    * Color del semáforo: `VERDE`, `AMBAR` o `ROJO` (RN-008).

### C. Recursos CRUD (ViewSets REST)
| Recurso | URL | Métodos permitidos | Descripción |
| :--- | :--- | :--- | :--- |
| **Delegaciones** | `/api/delegaciones/` | `GET`, `POST`, `PUT`, `DELETE` | Las 6 delegaciones oficiales |
| **Cargos** | `/api/cargos/` | `GET`, `POST`, `PUT`, `DELETE` | Catálogo de cargos municipales |
| **Usuarios** | `/api/usuarios/` | `GET`, `POST`, `PUT` | Gestión de usuarios con roles y 2FA |
| **Períodos** | `/api/periodos/` | `GET`, `POST`, `PUT` | Períodos trimestrales de medición |
| **Catálogo** | `/api/catalogos/` | `GET`, `POST` | Catálogo maestro de servicios |
| **Ítems Medición** | `/api/items-medicion/` | `GET`, `POST`, `PUT` | Metas cuantitativas y ponderadores |
| **Actividades** | `/api/actividades/` | `GET`, `POST`, `PUT`, `DELETE` | Registro de gestiones en terreno |
| **Evidencias** | `/api/evidencias/` | `GET`, `POST`, `PUT` | Fotos con código verificador SHA-256 |
| **Compromisos** | `/api/compromisos/` | `GET`, `POST`, `PUT` | Tubo de trabajo / agenda vecinal |
| **Casos Sociales**| `/api/casos-sociales/` | `GET`, `POST`, `PUT` | Casos vulnerables con RUT protegido |
| **Auditoría** | `/api/auditoria/` | `GET` (Read Only) | Log inmutable de cambios |

---

## 5. Reglas de Negocio Implementadas (`calculos.py`)

* **RN-001 (Ponderación 100%):** La suma de las ponderaciones de los ítems de un cargo en un período debe totalizar exactamente el 100%.
* **RN-005 (Tope 150%):** Ningún ítem puede computar más del 150% de cumplimiento para evitar que un solo ítem sobrecompense el abandono de otros.
* **RN-007 (Meta Esperada al Día):** Proporción lineal entre días transcurridos y días totales del período:
  $$\text{Meta Esperada (\%)} = \left(\frac{\text{Días Transcurridos}}{\text{Días Totales del Período}}\right) \times 100$$
* **RN-008 (Regla del Semáforo):**
  $$\text{Ratio} = \left(\frac{\text{Cumplimiento Real}}{\text{Meta Esperada al Día}}\right) \times 100$$
  * **VERDE:** Ratio >= 100% (Cumple o supera la meta proporcional esperada a la fecha).
  * **ÁMBAR:** 60% <= Ratio < 100% (Avance aceptable, en observación preventiva).
  * **ROJO:** Ratio < 60% (Alerta crítica por retraso significativo).
* **RN-009 (Filtro de Evidencia Aprobada):** Solo las actividades con evidencia fotográfica en estado `APROBADA` computan en el cálculo de avance.

---

## 6. Ejecución de Pruebas Unitarias

El backend incluye una batería completa de pruebas automatizadas:

```powershell
python manage.py test sgr_app
```
