from djoser import views as djoser_views
from users.models import CustomUser
from .serializers import UserSerializer


class UserViewSet(djoser_views.UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
