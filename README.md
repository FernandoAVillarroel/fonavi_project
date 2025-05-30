## Cómo poner en marcha localmente

1. **Clonar el repositorio**  
   ```bash
   git clone https://github.com/tu-usuario/fonavi_project.git
   cd fonavi_project

1.Crear y activar un entorno virtual

python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

3.Instalar dependencias

pip install -r requirements.txt

4. Configurar base de datos

Copiar settings.py y actualizar DATABASES con tus credenciales MySQL.

5. Aplicar migraciones

   python manage.py migrate

6. Crear un superusuario

   python manage.py createsuperuser
   
8. Ejecutar el servidor

   python manage.py runserver
