# La Serena - SGR (Sistema de Gestión de Recursos)

Repositorio vinculado con el proyecto Jira **MLS** (Municipalidad de La Serena).

## Jira Project

**Proyecto:** MLS  
**Workspace:** inacapmail-team  
**Tablero:** Timeline  

### Acceso directo al Jira
- [Ver tablero Jira - MLS](https://inacapmail-team-uzxvvgtm.atlassian.net/jira/software/projects/MLS/boards/2/timeline)

## Descripción

Este repositorio contiene el código del proyecto SGR (Sistema de Gestión de Recursos) para la Municipalidad de La Serena, desarrollado en Django con Python.

## Documentación del Proyecto

Toda la información necesaria para desarrollar está disponible en estos documentos:

### Inicio Rápido
1. **[SETUP-JIRA-GITHUB.md](SETUP-JIRA-GITHUB.md)** - Configuración inicial de Jira y GitHub (Fase 1)
2. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guía de contribución y setup del entorno local

### Desarrollo
3. **[CHEATSHEET.md](CHEATSHEET.md)** - Referencia rápida de comandos Git, Django y utilidades
4. **[WORKFLOW-EXAMPLE.md](WORKFLOW-EXAMPLE.md)** - Ejemplo completo de flujo de trabajo con caso real (MLS-3: CRUD de Empleados)

### Calidad y Testing
5. **[TESTING-STRATEGY.md](TESTING-STRATEGY.md)** - Estrategia de testing obligatoria (3 niveles + seguridad)
6. **[TESTING-TEMPLATES.md](TESTING-TEMPLATES.md)** - Templates listos para copiar y usar en tests

### Revisión y Merge
7. **[PULL_REQUEST-REVIEW.md](PULL_REQUEST-REVIEW.md)** - Guía completa de PRs, revisión de código y merge

### Trazabilidad
8. **[TRACEABILITY-MATRIX.md](TRACEABILITY-MATRIX.md)** - Matriz que vincula Requerimientos → User Stories → Commits → Tests

## Flujo de trabajo

1. Las tareas se crean y gestionan en Jira (proyecto MLS)
2. Los cambios se realizan en este repositorio siguiendo [WORKFLOW-EXAMPLE.md](WORKFLOW-EXAMPLE.md)
3. Los pull requests deben referenciar el issue de Jira correspondiente
4. Todos los cambios deben incluir tests (ver [TESTING-STRATEGY.md](TESTING-STRATEGY.md))

### Referenciación de issues

Para vincular un commit o PR con Jira, incluye el código del issue en el mensaje:

```
git commit -m "MLS-123: Descripción del cambio"
```

## Equipo

- **Dev 1** - Administrador del proyecto
- **Dev 2 (Matías)** - Desarrollador
- **Dev 3** - Desarrollador

## Próximos Pasos

- Si es tu primera vez, lee [CONTRIBUTING.md](CONTRIBUTING.md)
- Para ver un ejemplo práctico, consulta [WORKFLOW-EXAMPLE.md](WORKFLOW-EXAMPLE.md)
- Antes de hacer push, verifica [TESTING-STRATEGY.md](TESTING-STRATEGY.md)

## Contacto

Para más información sobre el proyecto, accede al [tablero de Jira](https://inacapmail-team-uzxvvgtm.atlassian.net/jira/software/projects/MLS/boards/2/timeline).
