# empleados/auth.py
def is_presidencia(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)
