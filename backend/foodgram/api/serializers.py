from django.db.models import F
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Ingredient, IngredientsAmount, Recipe,
                            Tag, ShoppingCart, FavoriteRecipe)
from users.models import Follow, User


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class IngredientsAmountSerializer(serializers.ModelSerializer):

    class Meta:
        model = IngredientsAmount
        fields = ('ingredient', 'recipe', 'amount')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=request.user, author=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    # ingredients = IngredientsAmountSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('ingredient__amount')
        )

    def create_ingredients(self, recipe, ingredients):
        print(ingredients)
        IngredientsAmount.objects.bulk_create([
            IngredientsAmount(
                recipe=recipe,
                amount=ingredient['amount'],
                ingredient=Ingredient.objects.get(id=ingredient['id']),
            ) for ingredient in ingredients
        ])
        return recipe

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Поле ingredients не может быть пустым'
            )
        ingredient_list = []
        for ingredient in ingredients:
            id = ingredient.get('id')
            amount = ingredient.get('amount')
            if int(amount) < 1:
                raise serializers.ValidationError(
                    'Минимальное количество ингредиентов 1'
                )
            if not Ingredient.objects.filter(id=id).exists():
                raise serializers.ValidationError(
                    f'Ингредиента c id {id} не существует'
                )
            if id in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиенты дублируются'
                )
            ingredient_list.append(id)
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Поле tags не может быть пустым'
            )
        for tag in tags:
            if not Tag.objects.filter(id=tag).exists():
                raise serializers.ValidationError(
                    f'Тега {tag} не существует'
                )
        return tags

    def validate_cooking_time(self, cooking_time):
        if cooking_time <= 0:
            raise serializers.ValidationError(
                'Время готовки должно быть больше 0'
            )
        return cooking_time

    def create(self, validated_data):
        print(validated_data)
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(self.initial_data.get('tags'))
        ingredients = self.initial_data.get('ingredients')
        return self.create_ingredients(recipe, ingredients)

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = self.validated_data.get('ingredients')
        instance.tags.set(self.initial_data.get('tags'))
        instance = self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)


class RecipeShortInfo(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, author):
        queryset = self.context.get('request')
        recipes_limit = queryset.query_params.get('recipes_limit')
        if not recipes_limit:
            return RecipeShortInfo(
                Recipe.objects.filter(author=author),
                many=True, context={'request': queryset}
            ).data
        return RecipeShortInfo(
            Recipe.objects.filter(author=author)[:int(recipes_limit)],
            many=True,
            context={'request': queryset}
        ).data

    def get_recipes_count(self, author):
        return Recipe.objects.filter(author=author).count()


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        get_object_or_404(User, username=data['author'])
        if self.context['request'].user == data['author']:
            raise serializers.ValidationError({
                'errors': 'Нельзя подписаться на самого себя.'
            })
        if Follow.objects.filter(
                user=self.context['request'].user,
                author=data['author']
        ):
            raise serializers.ValidationError({
                'errors': 'Уже подписан.'
            })
        return data

    def to_representation(self, value):
        return FollowListSerializer(
            value.author,
            context={'request': self.context.get('request')}
        ).data


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['recipe', 'user']
        model = ShoppingCart

    def validate(self, data):
        request = self.context.get('request')
        recipe = data['recipe']
        if ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            raise serializers.ValidationError({
                'errors': 'Данный рецепт уже есть в корзине.'
            })
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeShortInfo(instance.recipe, context=context).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')

    def validate(self, data):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        recipe = data['recipe']
        if FavoriteRecipe.objects.filter(
            user=request.user, recipe=recipe
        ).exists():
            raise serializers.ValidationError({
                'errors': 'Уже есть в избранном.'
            })
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeShortInfo(
            instance.recipe, context=context).data
