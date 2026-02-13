from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """Recipe categories (e.g., Italian, Mexican, Dessert)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Ingredients that can be used in recipes"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Main recipe model"""
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recipes")
    
    # Recipe details
    prep_time = models.PositiveIntegerField(help_text="Preparation time in minutes")
    cook_time = models.PositiveIntegerField(help_text="Cooking time in minutes")
    servings = models.PositiveIntegerField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    
    # Media
    image = models.ImageField(upload_to="recipe_images/", blank=True, null=True)
    
    # Relationships
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    ingredients = models.ManyToManyField(Ingredient, through="RecipeIngredient", related_name="recipes")
    
    # Instructions
    instructions = models.TextField(help_text="Step-by-step cooking instructions")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    
    # ML-related fields
    average_rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    total_ratings = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["category"]),
            models.Index(fields=["author"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("recipe_detail", kwargs={"pk": self.pk})

    def get_total_time(self):
        """Returns total time (prep + cook) in minutes"""
        return self.prep_time + self.cook_time


class RecipeIngredient(models.Model):
    """Many-to-Many relationship between Recipe and Ingredient with quantity"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=100, help_text="e.g., '2 cups', '1 tablespoon', '500g'")
    notes = models.CharField(max_length=200, blank=True, help_text="Optional notes about this ingredient")

    class Meta:
        unique_together = ["recipe", "ingredient"]
        ordering = ["ingredient__name"]

    def __str__(self):
        return f"{self.quantity} {self.ingredient.name} for {self.recipe.title}"


class Review(models.Model):
    """User reviews and ratings for recipes"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["recipe", "user"]  # One review per user per recipe
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.rating} stars for {self.recipe.title}"

    def save(self, *args, **kwargs):
        """Update recipe's average rating when review is saved"""
        super().save(*args, **kwargs)
        self.update_recipe_rating()

    def delete(self, *args, **kwargs):
        """Update recipe's average rating when review is deleted"""
        recipe = self.recipe
        super().delete(*args, **kwargs)
        recipe.refresh_from_db()
        self._update_recipe_rating_for_recipe(recipe)

    def update_recipe_rating(self):
        """Calculate and update the recipe's average rating"""
        self._update_recipe_rating_for_recipe(self.recipe)

    @staticmethod
    def _update_recipe_rating_for_recipe(recipe):
        """Helper method to update rating for a recipe"""
        reviews = Review.objects.filter(recipe=recipe)
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg("rating"))["rating__avg"]
            recipe.average_rating = round(avg_rating, 2)
            recipe.total_ratings = reviews.count()
        else:
            recipe.average_rating = 0.0
            recipe.total_ratings = 0
        recipe.save(update_fields=["average_rating", "total_ratings"])


class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    favorite_recipes = models.ManyToManyField(Recipe, blank=True, related_name="favorited_by")
    dietary_restrictions = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated dietary restrictions (e.g., 'vegetarian, gluten-free')"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
