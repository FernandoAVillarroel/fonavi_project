# 🏢 Sistema FONAVI - Liquidación de Sueldos IPVU

> Sistema integral de gestión de liquidaciones y preliquidaciones para empleados del Instituto Provincial de Vivienda y Urbanismo

[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.x-orange.svg)](https://www.mysql.com/)

---

## 📸 Capturas del Sistema

### Acceso al Sistema

![Pantalla de Login](https://github.com/FernandoAVillarroel/fonavi_project/blob/rama-admin-fernando/Screenshot_262.png?raw=true)
*Pantalla de inicio de sesión con autenticación segura*

### Gestión de Empleados

![Gestión de Empleados](https://github.com/FernandoAVillarroel/fonavi_project/blob/rama-admin-fernando/Screenshot_660.png?raw=true)
*Panel principal de administración de empleados*

### Simulación de Liquidaciones

![Liquidación Confirmada](https://github.com/FernandoAVillarroel/fonavi_project/blob/rama-admin-fernando/Screenshot_661.png?raw=true)
*Vista de liquidaciones confirmadas con recibos duales*

![Panel de Control](https://github.com/FernandoAVillarroel/fonavi_project/blob/5d6f43906d8aee8fcd161b9784105dd4052eea36/Screenshot_733.png)
*Dashboard con indicadores y métricas del sistema*

---

## ✨ Características Principales

- 🧮 **Cálculo automático de bonos FONAVI** con antigüedad del 2% anual
- 📊 **Gestión de suplementos múltiples** (zona, función, título, etc.)
- 📝 **Recibos duales** generados automáticamente para cada liquidación
- 🔄 **Control de estados** (Activo, Inactivo, Retención)
- 📅 **Gestión de períodos** con estados controlados (Abierto/Cerrado/Sin crear)
- 🔍 **Auditoría completa** con registro detallado de cambios
- 🔐 **Autenticación dual** (Panel Admin + Usuarios operativos)
- ⚡ **Eficiencia mejorada**: De 5-7 días a 2 horas de procesamiento
- 📱 **Interfaz responsive** optimizada con Bootstrap 5
- 🔔 **Sistema de notificaciones** automáticas por cambios de estado

---

## 🎯 Impacto del Sistema

Este sistema automatiza la liquidación de bonos FONAVI para más de **200 empleados** del IPVU, reduciendo:
- ✅ Tiempo de procesamiento: **de 5-7 días a 2 horas**
- ✅ Errores de cálculo: **eliminados por completo**
- ✅ Transparencia: **acceso inmediato a recibos y notificaciones**

---

[Resto de tu README actual...]

Tecnologías utilizadas
Backend

Python 3.13 – Lenguaje principal del proyecto.

Django 5.2.x – Framework web (MVC/MVT), auth, sesiones, mensajes, ORM.

Django ORM (QuerySets avanzados con Q, Subquery, OuterRef, Coalesce, Value, DecimalField, IntegerField).

Sistema de autenticación de Django (LoginRequiredMixin, contrib.auth, permisos y grupos según panel).

Mensajería de Django (django.contrib.messages) para alertas/feedback en UI.

Gestión de sesión para selección y persistencia de Periodo de trabajo.

Base de datos

MySQL 8.x – Motor de BD en producción/desarrollo.

Conector: mysqlclient (driver recomendado para Django + MySQL).

MySQL Workbench – Administración, inspección de datos y scripts SQL.

Vistas/consultas en BD para reportes (p.ej., vistas de categorías y displays).

Frontend

Django Templates + staticfiles – Render del lado servidor.

Bootstrap 5.2.2 (CDN) – Maquetado responsive y componentes.

Font Awesome 6.4.2 (CDN) – Íconos en paneles/menús.

Google Fonts (Lato) – Tipografía principal.

Componentes propios: Panel “Presidencia”, panel de Periodo con estados (Abierto/ Cerrado/ Sin crear) y esquema de colores (verde/rojo/gris).

Arquitectura y módulos del dominio

Apps Django separadas (ej.: empleados, autenticacion, etc.).

Modelos clave: Empleado, Categoria, Oficina, OficioJudicial, estructuras de Liquidación/Preliquidación, Calificación, Nivel Básico, etc.

Casos de uso: ABM de empleados y oficinas, gestión de categorías/suplementos, periodos de trabajo, listados filtrados por Periodo y Área, oficios judiciales y descuentos.

Herramientas de desarrollo

Git & GitHub – Control de versiones y ramas (rama-admin-fernando, manuel-front, etc.).

Visual Studio Code – Editor principal (con Python/Django extensions).

Entorno virtual: .venv para aislar dependencias.

Logging/Debug – Prints y logs en vistas (e.g., intentos de login y redirecciones).

Calidad, diagramas y documentación

draw.io / diagrams.net – ERD del modelo de datos.

PlantUML – Diagramas (PERT, de flujo/actividad) para Gestión de Proyectos.

Buenas prácticas Django: CBV (ListView/DetailView), separación de responsabilidades, validación de formularios, mensajes de usuario, patrones de consulta eficientes.

Seguridad y autenticación

Sesiones seguras (Periodo en sesión).

Login protegido con LoginRequiredMixin, vistas restringidas por rol.

Mensajes de error/éxito controlados y redirecciones post-login.

Despliegue (base)

Configuraciones por entorno (DEBUG vs. PROD).

Variables de entorno para credenciales de BD.

Archivos estáticos servidos por collectstatic en producción.

---

## Cómo poner en marcha el proyecto localmente

Sigue estos pasos para clonar el repositorio y ponerlo a funcionar en tu máquina.

### 1. Clonar el repositorio

```bash
# Reemplaza tu-usuario por tu nombre de usuario en GitHub
git clone https://github.com/FernandoAVillarroel/fonavi_project.git
cd fonavi_project
```

### 2. Crear y activar un entorno virtual

\*\*Windows (PowerShell)\*\*

```powershell
python -m venv .venv
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser  # Si no lo habías hecho
.\.venv\Scripts\Activate.ps1
```

\*\*macOS / Linux\*\*

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y ajusta tus credenciales de base de datos:

```bash
cp .env.example .env
# Edita .env con tu editor favorito
```

### 5. Ejecutar migraciones y cargar datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear un superusuario

```bash
python manage.py createsuperuser
```

### 7. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

Abre tu navegador en `http://127.0.0.1:8000/` e inicia sesión con el superusuario.

---

## Despliegue en producción

Revisa la guía oficial de Django para [despliegue en producción](https://docs.djangoproject.com/en/5.2/howto/deployment/).

---

## Estructura principal del proyecto

```
fona vi_project/
├── autenticacion/    # App de autenticación personalizada
├── empleados/        # App principal de gestión de empleados
├── fonavi_project/   # Configuración global (settings, urls, wsgi)
├── requirements.txt  # Dependencias Python
├── manage.py         # Script de administración de Django
└── README.md         # Esta documentación
```

---

## Contribuciones

¡Se aceptan PRs! Por favor revisa las [guías de contribución](CONTRIBUTING.md) antes de enviar.

---

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.
