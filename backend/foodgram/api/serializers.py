from django.db.models import F
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Ingredient, IngredientsAmount, Recipe, RecipeTag,
                            Tag)
from users.models import Follow, User


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


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
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time'
        )

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id', 'name', 'measurement_unit', amount=F('ingredient__amount')
        )

    def get_ingredients_tags(self, recipe, ingredients, tags):
        for ingredient in ingredients:
            current_ingredient = Ingredient.objects.get(
                id=ingredient.get('id')
            )
            IngredientsAmount.objects.update_or_create(
                ingredient=current_ingredient,
                amount=ingredient.get('amount'),
                recipe=recipe
            )
        if isinstance(tags, int):
            current_tag = Tag.objects.get(id=tags)
            RecipeTag.objects.update_or_create(tag=current_tag, recipe=recipe)
        else:
            for tag in tags:
                current_tag = Tag.objects.get(id=tag)
                RecipeTag.objects.update_or_create(
                    tag=current_tag,
                    recipe=recipe
                )
        return recipe

    def validate_ingredients(self, ingredients):
        if ingredients == []:
            raise serializers.ValidationError(
                'Поле ingredients не может быть пустым'
            )
        try:
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
        except TypeError:
            raise serializers.ValidationError(
                'Поле tags обязательно для заполнения'
            )
        return ingredients

    def validate_tags(self, tags):
        if tags == []:
            raise serializers.ValidationError(
                'Поле tags не может быть пустым'
            )
        try:
            for tag in tags:
                if not Tag.objects.filter(id=tag).exists():
                    raise serializers.ValidationError(
                        f'Тега {tag} не существует'
                    )
        except TypeError:
            raise serializers.ValidationError(
                'Поле tags обязательно для заполнения'
            )
        return tags

    def create(self, validated_data):
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        self.validate_ingredients(ingredients)
        self.validate_tags(tags)
        recipe = Recipe.objects.create(**validated_data)
        return self.get_ingredients_tags(recipe, ingredients, tags)

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        instance.tags.clear()
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        self.validate_ingredients(ingredients)
        self.validate_tags(tags)
        instance = self.get_ingredients_tags(instance, ingredients, tags)
        return super().update(instance, validated_data)


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        recipes = obj.author.recipes.all()
        return RecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.all().count()
