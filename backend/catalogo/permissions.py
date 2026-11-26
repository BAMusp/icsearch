from rest_framework.permissions import SAFE_METHODS, BasePermission


class LeituraLivreEscritaAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


def docente_do_usuario(usuario):
    if not usuario or not usuario.is_authenticated:
        return None
    return getattr(usuario, "docente", None)


class LeituraLivreEscritaDocenteDono(BasePermission):
    message = "Apenas o docente responsavel pode alterar este registro."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return docente_do_usuario(request.user) is not None

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return view.docente_dono(obj) == docente_do_usuario(request.user)