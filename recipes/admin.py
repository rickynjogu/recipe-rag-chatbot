from django.contrib import admin
from .models import Category, Ingredient, Recipe, RecipeIngredient, Review, UserProfile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "created_at"]
    search_fields = ["name", "description"]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "created_at"]
    search_fields = ["name", "description"]


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "category",
        "difficulty",
        "average_rating",
        "total_ratings",
        "created_at",
        "is_featured",
    ]
    list_filter = ["category", "difficulty", "is_featured", "created_at"]
    search_fields = ["title", "description", "author__username"]
    readonly_fields = ["average_rating", "total_ratings", "created_at", "updated_at"]
    inlines = [RecipeIngredientInline]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "description", "author", "category", "image")
        }),
        ("Cooking Details", {
            "fields": ("prep_time", "cook_time", "servings", "difficulty", "instructions")
        }),
        ("Metadata", {
            "fields": ("is_featured", "average_rating", "total_ratings", "created_at", "updated_at")
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["recipe", "user", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["recipe__title", "user__username", "comment"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "dietary_restrictions", "created_at"]
    search_fields = ["user__username", "bio", "dietary_restrictions"]
    filter_horizontal = ["favorite_recipes"]
