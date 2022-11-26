from django.db.models import BooleanField, Exists, F, OuterRef, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from users.models import Follow, User
from .filters import RecipeFilter, IngredientSearchFilter
from .pagination import CustomPageNumberPagination
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart, Tag)
from .serializers import (FollowSerializer, IngredientSerializer,
                          TagSerializer, RecipeSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return User.objects.all()

    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = (permissions.IsAuthenticated,)
        return super().get_permissions()

    @action(
        methods=['post', 'delete'], detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, id):
        user = self.request.user
        author = get_object_or_404(User, id=id)
        object_exist = user.follower.filter(author=author).exists()
        if request.method == 'POST':
            if object_exist or user.id == int(id):
                return Response({
                    'error': 'Возможно вы пытаетесь подписаться на самого себя'
                },
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription = Follow.objects.create(user=user, author=author)
            serializer = FollowSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not object_exist:
            return Response({
                'error': 'Объект не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        user.follower.filter(author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(permission_classes=(permissions.IsAuthenticated,), detail=False)
    def subscriptions(self, request, pk=None):
        user = self.request.user
        queryset = user.follower.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FollowSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = FollowSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            queryset = Recipe.objects.annotate(
                is_favorited=Exists(
                    user.author_of_favoritting.filter(recipe__pk=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    user.author_of_shopping_cart.filter(recipe__pk=OuterRef('pk'))
                ),
            )
        else:
            queryset = Recipe.objects.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField())
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_fav_shopping_cart(self, request, model, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)
        object_exist = model.objects.filter(user=user, recipe__id=pk).exists()
        if request.method == 'POST':
            if object_exist:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if not object_exist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        model.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post', 'delete'], detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def favorite(self, request, pk):
        model = FavoriteRecipe
        return self.add_fav_shopping_cart(request, model, pk)

    @action(
        methods=['post', 'delete'], detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        model = ShoppingCart
        return self.add_fav_shopping_cart(request, model, pk)

    @action(permission_classes=(permissions.IsAuthenticated,), detail=False)
    def download_shopping_list(self, request, pk=None):
        user = self.request.user
        shopping_cart = user.author_of_shopping_cart.all()
        shopping_cart_dict = {}
        for recipe in shopping_cart:
            values_list = recipe.recipe.ingredients.values(
                'name', 'measurement_unit', amount=F('ingredient__amount')
            )
            for values in values_list:
                name = values['name']
                amount = values['amount']
                measurement_unit = values['measurement_unit']
                if name in shopping_cart_dict:
                    shopping_cart_dict[name]['amount'] = (
                        shopping_cart_dict[name]['amount'] + amount
                    )
                else:
                    shopping_cart_dict[name] = {
                        'measurement_unit': measurement_unit,
                        'amount': amount,
                    }
        shopping_list = []
        for key, values in shopping_cart_dict.items():
            shopping_list.append(
                f'{key} - {values["amount"]} {values["measurement_unit"]}. \n'
            )
        filename = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
