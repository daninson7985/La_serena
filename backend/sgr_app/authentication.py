from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Permite llamadas API desde el cliente web móvil/terreno sin conflicto de CSRF token
    manteniendo la sesión activa del usuario.
    """
    def enforce_csrf(self, request):
        return