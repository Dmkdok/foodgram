from django.shortcuts import get_object_or_404
from djoser import views as djoser_views
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser, Follow

from .serializers import UserSerializer


class UserViewSet(djoser_views.UserViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(CustomUser, id=pk)

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Follow.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Уже подписаны'}, status=status.HTTP_400_BAD_REQUEST
            )

        Follow.objects.create(user=user, author=author)
        serializer = UserSerializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
    )
    def unsubscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(CustomUser, id=pk)
        try:
            follow = Follow.objects.get(user=user, author=author)
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Follow.DoesNotExist:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST,
            )
