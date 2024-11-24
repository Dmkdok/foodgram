from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAdminOrReadOnly(BasePermission):
    """
    Разрешение, позволяющее автору и администратору редактировать или удалять.
    Остальным только чтение.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_authenticated and (
            request.user.is_staff or obj.author == request.user
        )
