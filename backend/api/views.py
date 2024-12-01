from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import CustomUser
from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPaginator
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    AvatarSerializer,
    CustomUserSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    ShortRecipeSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UnfollowSerializer,
)


class UserViewSet(DjoserUserViewSet):
    """ViewSet для работы с пользователями."""

    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPaginator
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def me(self, request, *args, **kwargs):
        """Просмотр информации о пользователе."""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        url_name='me-avatar',
        permission_classes=(IsAuthenticated,),
    )
    def update_avatar(self, request):
        """Обновление аватара текущего пользователя."""
        user = self.request.user
        serializer = AvatarSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'avatar': serializer.data['avatar']},
            status=status.HTTP_200_OK,
        )

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара текущего пользователя."""
        request.user.avatar.delete()
        request.user.save()
        return Response(
            {'message': 'Аватар удален'}, status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """Список подписок пользователя."""
        queryset = CustomUser.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id=None):
        """Подписка на автора."""
        author = get_object_or_404(CustomUser, id=id)
        serializer = FollowSerializer(
            data={'author': author.id}, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отписка от автора."""
        serializer = UnfollowSerializer(
            data={}, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        response_data = serializer.delete(serializer.validated_data)
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend,)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        """Получение queryset с учетом аутентификации пользователя."""
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.prefetch_related('favorites', 'shopping_cart')
        return queryset

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in SAFE_METHODS:
            return RecipeListSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        """Сохраняет рецепт с автором."""
        user = self.request.user
        if user.is_anonymous:
            raise NotAuthenticated("Пользователь должен быть аутентифицирован")
        serializer.save(author=user)

    def redirect_to_short_link(self, request, pk):
        """Перенаправляет на страницу рецепта по короткой ссылке."""
        return redirect(f'/recipes/{pk}/')

    def _add_to_model(self, model, request, pk, error_message):
        """
        Общий метод для добавления рецепта в модель
        (избранное или список покупок).
        """
        recipe = get_object_or_404(Recipe, id=pk)

        if model.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': error_message}, status=status.HTTP_400_BAD_REQUEST
            )

        model.objects.create(user=request.user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_model(self, model, request, pk, error_message):
        """
        Общий метод для удаления рецепта из модели
        (избранное или список покупок).

        """
        recipe = get_object_or_404(Recipe, id=pk)

        try:
            instance = model.objects.get(user=request.user, recipe=recipe)
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except model.DoesNotExist:
            return Response(
                {'errors': error_message}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Добавляет/удаляет рецепт в/из избранного."""
        if request.method == 'POST':
            return self._add_to_model(
                Favorite, request, pk, 'Рецепт успешно добавлен в избранное'
            )

        return self._remove_from_model(
            Favorite, request, pk, 'Рецепт успешно удален из избранного'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Добавляет/удаляет рецепт в/из списка покупок."""
        if request.method == 'POST':
            return self._add_to_model(
                ShoppingCart,
                request,
                pk,
                'Рецепт успешно добавлен в список покупок',
            )

        return self._remove_from_model(
            ShoppingCart,
            request,
            pk,
            'Рецепт успешно удален из списка покупок',
        )

    @action(detail=True, methods=['GET'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """
        Генерация короткой ссылки с использованием ID рецепта.
        """
        try:
            recipe = self.get_object()
            base_url = request.build_absolute_uri('/').rstrip('/')
            short_link = f'{base_url}/s/{recipe.id}'

            return Response(
                {'short-link': short_link}, status=status.HTTP_200_OK
            )

        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Рецепт не найден'}, status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """
        Формирует и возвращает список покупок пользователя в текстовом формате.
        """
        ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        if not ingredients:
            return Response(
                {'errors': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shopping_list = ['Список покупок:']
        for ingredient in ingredients:
            shopping_list.append(
                f'{ingredient["ingredient__name"]} '
                f'({ingredient["ingredient__measurement_unit"]}) - '
                f'{ingredient["total_amount"]}'
            )

        shopping_list_text = '\n'.join(shopping_list)
        response = HttpResponse(
            shopping_list_text, content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )

        return response
