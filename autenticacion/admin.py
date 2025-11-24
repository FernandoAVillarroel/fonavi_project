from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import Usuarios

@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nombre', 'email', 'tipo_display')
    list_filter = ('tipo',)
    search_fields = ('nombre', 'email')
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('nombre', 'email', 'tipo')
        }),
        ('Contraseña', {
            'fields': ('contrasena',),
            'description': '⚠️ La contraseña se guarda en texto plano. Escríbela directamente.'
        }),
    )
    
    def tipo_display(self, obj):
        return "👑 Administrador" if obj.tipo == 1 else "👤 Sueldos"
    tipo_display.short_description = 'Rol'
    
    def save_model(self, request, obj, form, change):
        # Guardar tal cual (texto plano)
        super().save_model(request, obj, form, change)