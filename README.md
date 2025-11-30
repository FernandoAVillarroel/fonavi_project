# 🏢 Sistema FONAVI - Liquidación de Sueldos IPVU

Sistema integral de gestión de empleados, preliquidaciones y liquidaciones salariales para el Instituto Provincial de Vivienda y Urbanismo (IPVU).

### 💡 ¿Qué hace?
Gestiona más de 600 empleados y automatiza el proceso completo de:
- Preliquidaciones con cálculos de antigüedad (2% anual), suplementos y embargos
- Liquidaciones confirmadas que se exportan automáticamente
- Generación de archivos TXT para la Dirección de Informática de la Provincia

### 🎯 Impacto
- ⏱️ Reduce el tiempo de procesamiento de **5-7 días a 2 horas**
- ✅ Elimina errores de cálculo manual
- 🔄 Integración directa con sistemas provinciales
- 🔒 Liquidaciones confirmadas no modificables (integridad de datos)

### 🛠️ Tecnologías

**Backend:**
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.x-orange.svg)](https://www.mysql.com/)

**Frontend:**
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26.svg?logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6.svg?logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)

**Estado del Proyecto:**
![Status](https://img.shields.io/badge/Estado-En%20Desarrollo-brightgreen.svg)
![Versión](https://img.shields.io/badge/Versión-1.0-blue.svg)
---

## 📸 Capturas del Sistema

### Acceso al Sistema

<img width="1913" height="1038" alt="Screenshot_262" src="https://github.com/user-attachments/assets/8e88936d-71dc-4698-bf29-b2fdc98e1d80" />

*Pantalla de inicio de sesión con autenticación segura*

### Gestión de Empleados

![Gestión de Empleados](https://github.com/FernandoAVillarroel/fonavi_project/blob/rama-admin-fernando/Screenshot_660.png?raw=true)
*Panel principal de administración de empleados*

### Simulación de Liquidaciones

<img width="1916" height="1026" alt="Screenshot_266" src="https://github.com/user-attachments/assets/fee86abb-6977-4281-adbf-f91f71e90b9b" />

*Vista de liquidaciones confirmadas con recibos duales*

<img width="1919" height="1035" alt="Screenshot_263" src="https://github.com/user-attachments/assets/86c3f1d6-be50-4275-89a1-2fbd9128a36c" />

*Vista detallada de liquidaciones confirmadas con:*
- Totales generales (empleados, bruto, descuentos, líquido)
- Desglose completo por empleado con todos los suplementos
- Filtros por tipo de agente
- Exportación a PDF, TXT y Contribuciones Patronales
---

## ✨ Características Principales

**🧮 Cálculos Automáticos**
* Bonos FONAVI con antigüedad del 2% anual
* Múltiples suplementos (zona, función, título, etc.)
* Embargos judiciales y descuentos
* Validación automática de errores

**📊 Gestión Integral**
* 600+ empleados activos e inactivos
* Preliquidaciones editables
* Liquidaciones confirmadas (bloqueadas permanentemente)
* Control de estados (Activo/Inactivo/Retención)
* Gestión de períodos (Abierto/Cerrado/Sin crear)

**📤 Exportación Multi-formato**
* TXT → Dirección de Informática Provincial
* PDF → Recibos individuales
* Reportes → Contribuciones Patronales
* Vista detallada con totales y desgloses

**🔐 Seguridad y Auditoría**
* Autenticación dual (Admin + Operativo)
* Registro completo de cambios
* Notificaciones automáticas
* Períodos con control de acceso

**📱 Experiencia de Usuario**
* Interfaz responsive (Bootstrap 5)
* Panel de control intuitivo
* Filtros dinámicos por área/tipo
* Sistema de notificaciones mensual

## 🎯 Impacto Medible

✅ **Tiempo:** 5-7 días → 2 horas (95% más rápido)  
✅ **Precisión:** 100% - cero errores de cálculo  
✅ **Empleados:** Gestión de 600+ empleados  
✅ **Transparencia:** Auditoría completa + notificaciones automáticas  
✅ **Integración:** Exportación directa a sistemas provinciales

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.13** - Lenguaje principal del proyecto
- **Django 5.2.x** - Framework web (MVT)
  - Sistema de autenticación (`LoginRequiredMixin`, `contrib.auth`, permisos y grupos)
  - Mensajería (`django.contrib.messages`) para alertas y feedback
  - Gestión de sesiones para persistencia de Período de trabajo
- **Django ORM Avanzado**
  - QuerySets con `Q`, `Subquery`, `OuterRef`, `Coalesce`, `Value`
  - Operaciones con `DecimalField`, `IntegerField`
  - Vistas y consultas optimizadas

### Base de Datos
- **MySQL 8.x** - Motor principal (producción/desarrollo)
- **mysqlclient** - Driver recomendado para Django + MySQL
- **MySQL Workbench** - Administración e inspección de datos
- Vistas SQL personalizadas para reportes (categorías, displays)

### Frontend
- **Django Templates** + `staticfiles` - Renderizado del lado del servidor
- **Bootstrap 5.2.2** (CDN) - Framework CSS responsive
- **Font Awesome 6.4.2** (CDN) - Sistema de iconos
- **Google Fonts (Lato)** - Tipografía principal
- **Componentes personalizados:**
  - Panel "Presidencia"
  - Panel de Período con estados visuales (Abierto/Cerrado/Sin crear)
  - Esquema de colores dinámico (verde/rojo/gris)

### Arquitectura
- **Apps Django separadas** por dominio:
  - `empleados` - Gestión de personal
  - `autenticacion` - Sistema de login dual
  - *(otras apps del proyecto)*
  
- **Modelos principales:**
  - `Empleado`, `Categoria`, `Oficina`
  - `OficioJudicial`, `Liquidacion`, `Preliquidacion`
  - `Calificacion`, `NivelBasico`, suplementos

- **Casos de uso:**
  - ABM de empleados y oficinas
  - Gestión de categorías y suplementos
  - Administración de períodos de trabajo
  - Listados filtrados por Período y Área
  - Procesamiento de oficios judiciales y descuentos

### Herramientas de Desarrollo
- **Git & GitHub** - Control de versiones
  - Ramas: `rama-admin-fernando`, `manuel-front`
- **Visual Studio Code** - Editor principal
  - Extensions: Python, Django
- **Entorno virtual** - `.venv` para aislamiento de dependencias
- **Logging/Debug** - Registro de eventos y debugging

### Calidad y Documentación
- **draw.io / diagrams.net** - Diagramas ERD del modelo de datos
- **PlantUML** - Diagramas PERT y de flujo para Gestión de Proyectos
- **Buenas prácticas Django:**
  - Class-Based Views (`ListView`, `DetailView`)
  - Separación de responsabilidades
  - Validación de formularios
  - Patrones de consulta eficientes

### Seguridad
- 🔒 Sesiones seguras (Período en sesión)
- 🔐 Login protegido con `LoginRequiredMixin`
- 👥 Vistas restringidas por rol
- ✅ Mensajes de error/éxito controlados
- 🔄 Redirecciones seguras post-login

### Despliegue
- ⚙️ Configuraciones por entorno (`DEBUG` vs. `PROD`)
- 🔑 Variables de entorno para credenciales
- 📦 Archivos estáticos con `collectstatic`

---

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.13+
- MySQL 8.x
- Git

### 1️⃣ Clonar el Repositorio
```bash
git clone https://github.com/FernandoAVillarroel/fonavi_project.git
cd fonavi_project
```

### 2️⃣ Crear y Activar Entorno Virtual

**Windows (PowerShell)**
```powershell
python -m venv .venv
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser  # Solo si es necesario
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4️⃣ Configurar Variables de Entorno
```bash
cp .env.example .env
# Edita .env con tus credenciales de MySQL
```

**Ejemplo de `.env`:**
```env
DB_NAME=fonavi_db
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
```

### 5️⃣ Ejecutar Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6️⃣ Crear Superusuario
```bash
python manage.py createsuperuser
```

### 7️⃣ Iniciar Servidor de Desarrollo
```bash
python manage.py runserver
```

🌐 Abre tu navegador en **http://127.0.0.1:8000/** e inicia sesión con el superusuario.

---

## 📁 Estructura del Proyecto
```
fonavi_project/
├── autenticacion/       # App de autenticación personalizada
├── empleados/           # App principal de gestión de empleados
├── fonavi_project/      # Configuración global (settings, urls, wsgi)
├── static/              # Archivos estáticos (CSS, JS, imágenes)
├── templates/           # Plantillas HTML globales
├── .env.example         # Ejemplo de variables de entorno
├── requirements.txt     # Dependencias Python
├── manage.py            # Script de administración Django
└── README.md            # Documentación del proyecto
```

---

## 📚 Despliegue en Producción

Para desplegar en producción, consulta la [guía oficial de Django](https://docs.djangoproject.com/en/5.2/howto/deployment/).

**Checklist de producción:**
- [ ] `DEBUG = False` en settings
- [ ] Configurar `ALLOWED_HOSTS`
- [ ] Usar servidor web (Nginx/Apache)
- [ ] Configurar WSGI (Gunicorn/uWSGI)
- [ ] Habilitar HTTPS
- [ ] Configurar backups de BD
- [ ] Ejecutar `collectstatic`

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es de uso interno del **Instituto Provincial de Vivienda y Urbanismo (IPVU)**.

---

## 📞 Contacto

**Equipo de Desarrollo FONAVI**
- 📧 Email: [correo del equipo]
- 🏢 IPVU - Santiago del Estero

---

**Desarrollado con ❤️ para IPVU**
