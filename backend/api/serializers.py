from django.core.validators import MinValueValidator
from django.forms import ValidationError
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import CustomUser, Follow


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя."""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        """
        Создает и возвращает нового пользователя с зашифрованным паролем.
        """
        user = CustomUser.objects.create_user(**validated_data)
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """
        Проверяет, подписан ли текущий пользователь на данного автора.
        """
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    avatar = Base64ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ('avatar',)

    def update(self, instance, validated_data):
        """Обновляет аватар пользователя."""
        avatar = validated_data.get('avatar')
        if avatar is not None:
            instance.avatar = avatar
            instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка рецептов."""
    tags = TagSerializer(many=True, read_only=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def check_recipe_status(self, recipe, status_model):
        """
        Проверяет статус рецепта (в избранном или в списке покупок)
        для текущего пользователя.
        """
        current_request = self.context.get('request')

        if not current_request or current_request.user.is_anonymous:
            return False

        return status_model.objects.filter(
            user=current_request.user, recipe=recipe
        ).exists()

    def get_is_favorited(self, recipe):
        """
        Проверяет, находится ли рецепт в избранном
        у текущего пользователя.
        """
        return self.check_recipe_status(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        """
        Проверяет, находится ли рецепт в списке покупок
        у текущего пользователя.
        """
        return self.check_recipe_status(recipe, ShoppingCart)


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов в рецепт."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(1, message=f'Количество должно быть больше {0}'),
        ),
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""
    author = CustomUserSerializer(required=False)
    image = Base64ImageField(required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = IngredientWriteSerializer(
        many=True, required=True, source='recipe_ingredients'
    )
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(1, message=f'Время должно быть больше {0}'),
        ),
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'author',
            'text',
            'cooking_time',
        )

    def validate_image(self, image):
        """Валидация изображения."""
        if image is None:
            raise serializers.ValidationError(
                'Необходимо добавить изображение.'
            )
        return image

    def get_ingredients_in_recipe(self, recipe, ingredients):
        """Создает объекты RecipeIngredient для рецепта."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                ingredient=ingredient['ingredient'],
                recipe=recipe,
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        """Создает новый рецепт."""
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.get_ingredients_in_recipe(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        """Обновляет существующий рецепт."""
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.get_ingredients_in_recipe(instance, ingredients)
        instance.tags.remove()
        instance.tags.set(tags)
        return super().update(instance, validated_data)

    def validate(self, value):
        """Общая валидация данных."""
        tags = value.get('tags')
        ingredients = value.get('recipe_ingredients')
        if not tags:
            raise serializers.ValidationError(
                'Теги не могут быть пустыми',
            )
        if not ingredients:
            raise serializers.ValidationError(
                'Ингредиенты не могут быть пустыми',
            )
        return value

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        if not value:
            raise ValidationError('Ни один ингредиент не выбран')
        ingredients_set = set()
        for item in value:
            ingredient = item.get('ingredient')
            print(f"Validating ingredient: {item}")
            if ingredient is None:
                raise ValidationError('Ингредиент должен быть указан')
            if ingredient in ingredients_set:
                raise ValidationError('Ингредиенты должны быть уникальными')
            ingredients_set.add(ingredient)
        return value

    def validate_tags(self, value):
        """Валидация тэгов."""
        if not value:
            raise ValidationError('Не выбраны теги')
        tags_set = set()
        for tag in value:
            if tag in tags_set:
                raise ValidationError('Теги должны быть уникальными')
            tags_set.add(tag)
        return value

    def to_representation(self, instance):
        """Возвращает представление рецепта с помощью RecipeListSerializer."""
        return RecipeListSerializer(instance, context=self.context).data


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора',
            )
        ]

    def validate_author(self, value):
        """
        Проверяет, что пользователь не пытается подписаться
        на самого себя.
        """
        if self.context['request'].user == value:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя'
            )
        return value

    def to_representation(self, instance):
        """Возвращает представление автора, на которого подписались."""
        return SubscriptionSerializer(
            instance.author, context=self.context
        ).data


class UnfollowSerializer(serializers.Serializer):
    """Сериализатор для отписки."""

    def validate(self, data):
        """Проверяет, что пользователь подписан на автора."""
        user = self.context['request'].user
        author = self.context['view'].get_object()

        if not Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы не подписаны на этого автора.'
            )

        return data

    def delete(self, validated_data):
        """Отписывает пользователя от автора."""
        author = self.context['view'].get_object()
        Follow.objects.filter(
            user=self.context['request'].user, author=author
        ).delete()
        return {'detail': f'Вы успешно отписались от {author.username}!'}


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного автора."""
        user = self.context['request'].user
        return Follow.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        """Возвращает рецепты автора с учетом параметра recipes_limit."""
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        if recipes_limit is not None:
            recipes = obj.recipes.all()[: int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return ShortRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Возвращает общее количество рецептов автора."""
        return obj.recipes.count()
