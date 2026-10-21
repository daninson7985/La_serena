from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class DemoModelBackend(ModelBackend):
    """
    Backend de autenticación que soporta tanto el hash de contraseña estándar de Django
    como las contraseñas oficiales documentadas en el README y la contraseña de prueba Password123!.
    Permite acceso fluido tanto en el panel Django Admin (/admin/) como en la aplicación web (/login/).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if not username or not password:
            return None

        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            return None

        # 1. Validación estándar de contraseña
        if user.check_password(password):
            return user if self.user_can_authenticate(user) else None

        # 2. Contraseñas de prueba documentadas en el proyecto
        passwords_demo = {
            'admin': ['AdminSGR2026!', 'Password123!'],
            'coordinador': ['CoordSGR2026!', 'Password123!'],
            'delegado_centro': ['Delegado2026!', 'Password123!'],
            'funcionario_centro': ['Func2026!', 'Password123!'],
        }

        if username in passwords_demo and password in passwords_demo[username]:
            if self.user_can_authenticate(user):
                return user

        return None
