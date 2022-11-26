from django.urls import include, path
from rest_framework import routers

from .views import (TagViewSet, IngredientViewSet,
                    CustomUserViewSet, RecipeViewSet)

app_name = 'api'

router = routers.DefaultRouter()

router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('users', CustomUserViewSet)
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
