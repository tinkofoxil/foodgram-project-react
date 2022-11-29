from django.db.models.aggregates import Sum
from django.db.models import BooleanField, Exists, F, OuterRef, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from users.models import Follow, User
from .pagination import CustomPageNumberPagination
from .filters import RecipeFilter, IngredientSearchFilter
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart, Tag, IngredientsAmount)
from .serializers import (FollowSerializer, IngredientSerializer, CartSerializer,
                          TagSerializer, RecipeSerializer, FavoriteSerializer)


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
        if request.method != 'POST':
            subscription = get_object_or_404(
                Follow,
                author=get_object_or_404(User, id=id),
                user=request.user
            )
            self.perform_destroy(subscription)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = FollowSerializer(
            data={
                'user': request.user.id,
                'author': get_object_or_404(User, id=id).id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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

    @staticmethod
    def post_method_for_actions(request, pk, serializers):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = serializers(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @staticmethod
    def delete_method_for_actions(request, pk, model):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        model_instance = get_object_or_404(model, user=user, recipe=recipe)
        model_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

    @action(
        methods=['post'], detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        return self.post_method_for_actions(
            request, pk, serializers=CartSerializer
        )
    
    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.delete_method_for_actions(
            request=request, pk=pk, model=ShoppingCart)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk):
        return self.post_method_for_actions(
            request=request, pk=pk, serializers=FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self.delete_method_for_actions(
            request=request, pk=pk, model=FavoriteRecipe)

    @action(permission_classes=(permissions.IsAuthenticated,), detail=False)
    def download_shopping_cart(self, request, pk=None):
        user = request.user

        shopping_cart = IngredientsAmount.objects.filter(
            recipe__shopping_cart__user=user).values(
                'ingredient__name',
                'ingredient__measurement_unit').annotate(amount=Sum('amount'))
        shopping_cart_dict = {}
        for recipe in shopping_cart:
            name = recipe['ingredient__name']
            amount = recipe['amount']
            measurement_unit = recipe['ingredient__measurement_unit']
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
