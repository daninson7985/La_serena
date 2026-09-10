# Guía de Contribución - La Serena

¡Bienvenido al proyecto! Esta guía te ayudará a configurar tu entorno de desarrollo y a seguir el flujo de trabajo del equipo.

---

## 📋 Fase 1: Configuración Inicial del Proyecto (Dev 1)

El desarrollador principal ya ha inicializado el repositorio y subido el código base a GitHub. Si eres Dev 2 o Dev 3, sigue la **Fase 2** a continuación.

---

## 🚀 Fase 2: Unirse al Proyecto (Dev 2 y Dev 3)

Sigue estos pasos para configurar tu entorno local:

### Paso 1: Clonar el repositorio
```powershell
git clone https://github.com/daninson7985/La_serena.git
```

### Paso 2: Acceder a la carpeta del proyecto
```powershell
cd La_serena
```

### Paso 3: Crear y activar el entorno virtual
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Nota:** Si ves `(venv)` al inicio de tu línea de comandos, significa que el entorno virtual está activado correctamente.

### Paso 4: Instalar las dependencias del proyecto
```powershell
pip install -r requirements.txt
```

### Paso 5: Ejecutar las migraciones iniciales
Esto crea la base de datos local con la estructura necesaria:
```powershell
python manage.py migrate
```

### Paso 6: Verificar que todo funciona correctamente
Inicia el servidor de desarrollo:
```powershell
python manage.py runserver
```

Deberías ver algo como:
```
Starting development server at http://127.0.0.1:8000/
```

¡Si ves este mensaje, estás listo para trabajar! 🎉

---

## 💼 Fase 3: Flujo de Trabajo Diario

### ⚠️ REGLA DE ORO
**NADIE programa directamente en la rama `main`.** La rama `main` solo contiene código probado y funcional.

### 📊 Ciclo de trabajo para cada tarea

Cada vez que tomes una nueva tarea, sigue estos pasos **en orden estricto**:

#### 1️⃣ En Jira
- Abre tu tablero Jira
- Toma el ticket que vayas a trabajar
- Muévelo a la columna **"In Progress"**

#### 2️⃣ Actualizar tu código local
Antes de crear una rama nueva, asegúrate de tener la última versión:
```powershell
git checkout main
git pull origin main
```

#### 3️⃣ Crear tu rama de trabajo
Crea una rama nueva con el formato: `feature/SCRUM-XX-descripcion`

```powershell
git checkout -b feature/SCRUM-7-catalogo-productos
```

**Nomenclatura:**
- `feature/` para nuevas funcionalidades
- `SCRUM-XX` es el ID de tu ticket en Jira
- Descripción corta en minúsculas con guiones

#### 4️⃣ Trabajar y hacer commits
Desarrolla tu código y realiza commits regulares:
```powershell
git add .
git commit -m "SCRUM-7: Implementar listado de productos"
git commit -m "SCRUM-7: Agregar filtros al catálogo"
```

**Importante:** Siempre incluye el ID de Jira (ej. `SCRUM-7:`) al inicio del mensaje de commit. Esto vincula automáticamente tu trabajo a la tarjeta de Jira.

#### 5️⃣ Subir tu rama a GitHub
```powershell
git push origin feature/SCRUM-7-catalogo-productos
```

La primera vez que hagas `push`, GitHub puede pedirte que autorices la conexión en tu navegador.

---

## 📝 Convenciones de Commit

Sigue estas convenciones para mantener el histórico limpio y legible:

- **Formato:** `SCRUM-XX: Descripción clara y concisa`
- **Ejemplos válidos:**
  - `SCRUM-7: Crear modelo de Productos`
  - `SCRUM-7: Agregar serializer para API de productos`
  - `SCRUM-7: Implementar vista de listado de productos`

- **Ejemplos inválidos:**
  - `cambios` ❌
  - `fix bug` ❌
  - `actualización` ❌

---

## 🔄 Flujo completo de ejemplo

Imaginemos que tomas el ticket **SCRUM-7: Implementar catálogo de productos**

```powershell
# 1. Actualizar rama main
git checkout main
git pull origin main

# 2. Crear rama de trabajo
git checkout -b feature/SCRUM-7-catalogo-productos

# 3. Desarrollar (hacer cambios en los archivos)
# ... editas archivos, creas modelos, etc ...

# 4. Hacer commits
git add .
git commit -m "SCRUM-7: Crear modelo Product"

# ... más desarrollo ...

git add .
git commit -m "SCRUM-7: Agregar API endpoint para listar productos"

# 5. Subir rama a GitHub
git push origin feature/SCRUM-7-catalogo-productos

# 6. En GitHub/Jira: Crear Pull Request y pedir revisión del equipo
```

---

## 🐛 Solución de problemas comunes

### Problema: "fatal: not a git repository"
**Solución:** Asegúrate de estar en la carpeta del proyecto:
```powershell
cd La_serena
```

### Problema: El servidor no inicia
**Solución:** Verifica que el entorno virtual esté activado:
```powershell
.\venv\Scripts\activate
```

### Problema: Conflictos de merge
**Solución:** Antes de hacer cambios, siempre actualiza:
```powershell
git checkout main
git pull origin main
git checkout -b feature/SCRUM-XX-...
```

### Problema: "Permission denied" al hacer push
**Solución:** Es probable que sea la primera vez. GitHub te pedirá autorización en el navegador.

---

## 📞 Contacto y preguntas

Si tienes dudas sobre:
- **Configuración:** Consulta a Dev 1
- **Jira:** Revisa la documentación del tablero
- **Git:** Usa `git help [comando]` (ej. `git help commit`)

---

## ✅ Checklist inicial

Antes de tu primer commit, verifica:
- [ ] Ambiente virtual activado: `(venv)` en la línea de comandos
- [ ] Dependencias instaladas: `pip list | grep -i django`
- [ ] Servidor inicia sin errores: `python manage.py runserver`
- [ ] Tienes la rama main actualizada: `git pull origin main`
- [ ] Tu rama de trabajo existe: `git branch` debe mostrar tu rama

---

**¡Feliz a codear! 🚀**
