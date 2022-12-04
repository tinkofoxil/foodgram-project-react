from django.db.models import ExpressionWrapper, Q, BooleanField
from django_filters import AllValuesMultipleFilter, BooleanFilter, FilterSet
from django_filters.widgets import BooleanWidget
from django_filters.rest_framework import Filter
from rest_framework.filters import SearchFilter
from recipes.models import Recipe


class RecipeFilter(FilterSet):
    author = AllValuesMultipleFilter(field_name='author__id')
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_in_shopping_cart = BooleanFilter(
        field_name='is_in_shopping_cart',
        widget=BooleanWidget()
    )
    is_favorited = BooleanFilter(
        field_name='is_favorited',
        widget=BooleanWidget()
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']


class IngredientSearchFilter(SearchFilter):
    name = Filter(
        method='filter_name'
    )

    def filter_name(self, queryset, name, value):
        data = queryset.filter(name__contains=value)
        startswith = ExpressionWrapper(
            Q(name__startswith=value),
            output_field=BooleanField()
        )
        return data.annotate(startswith=startswith).order_by('-startswith')
