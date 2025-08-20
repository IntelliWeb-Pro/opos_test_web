# tests/permissions.py
from rest_framework.permissions import BasePermission

class IsSubscribed(BasePermission):
    message = "Funcionalidad premium: requiere suscripción activa."

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        return hasattr(u, 'suscripcion') and bool(getattr(u.suscripcion, 'activa', False))
