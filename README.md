## Proyecto Fonavi

Este proyecto Django **Fonavi** te permite gestionar preliquidaciones y liquidaciones de empleados, así como aplicar descuentos por oficios judiciales.

### Tecnologías

* Python 3.13
* Django 5.2.3
* MySQL (o MariaDB)

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
