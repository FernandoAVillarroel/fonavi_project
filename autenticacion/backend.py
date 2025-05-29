from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User, Group
from .models import Usuarios

class UsuariosBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        # Debug: mostrar lo que recibe
        print(f"[DEBUG] Login intento: username={username!r}, password={password!r}")

        try:
            u = Usuarios.objects.get(nombre=username)
        except Usuarios.DoesNotExist:
            print("[DEBUG] Usuario no existe en tabla Usuarios")
            return None

        # Debug: mostrar contraseña almacenada
        print(f"[DEBUG] Contraseña en DB: {u.contrasena!r}")

        if u.contrasena == password:
            print("[DEBUG] ¡Coinciden!")
            user, _ = User.objects.get_or_create(username=username)
            user.email = u.email
            user.is_staff = True
            user.set_unusable_password()

            # Grupos
            sueldos_group, _ = Group.objects.get_or_create(name='Sueldos')
            admin_group,  _   = Group.objects.get_or_create(name='Administradores')
            user.groups.clear()
            if u.tipo == 1:
                user.groups.add(admin_group)
                user.is_superuser = True
            elif u.tipo == 2:
                user.groups.add(sueldos_group)
                user.is_superuser = False

            user.save()
            return user

        print("[DEBUG] NO coinciden")
        return None

    def get_user(self, user_id):
        return User.objects.filter(pk=user_id).first()


