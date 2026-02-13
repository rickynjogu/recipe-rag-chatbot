from django.urls import path
from . import views

app_name = "recipes"

urlpatterns = [
    path("", views.RecipeListView.as_view(), name="recipe_list"),
    path("<int:pk>/", views.RecipeDetailView.as_view(), name="recipe_detail"),
    path("create/", views.RecipeCreateView.as_view(), name="recipe_create"),
    path("<int:pk>/edit/", views.RecipeUpdateView.as_view(), name="recipe_edit"),
    path("<int:pk>/delete/", views.RecipeDeleteView.as_view(), name="recipe_delete"),
    path("category/<int:pk>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("search/", views.RecipeSearchView.as_view(), name="recipe_search"),
]
