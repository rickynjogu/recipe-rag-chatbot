"""
Django Shell Examples - Copy and paste these into Django shell
Run: python manage.py shell
Then copy/paste sections below
"""

# ============================================
# STEP 1: Import Models
# ============================================
from recipes.models import Recipe, Category, Ingredient, Review, RecipeIngredient
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Sum, Q, F
from django.utils import timezone

# ============================================
# STEP 2: CREATE Objects
# ============================================

# Get or create a user
user, created = User.objects.get_or_create(
    username="chef_mario",
    defaults={
        "email": "mario@example.com",
        "first_name": "Mario",
        "last_name": "Chef"
    }
)
if created:
    user.set_password("test123")
    user.save()
    print(f"✅ Created user: {user.username}")
else:
    print(f"✅ Using existing user: {user.username}")

# Create categories
italian, _ = Category.objects.get_or_create(
    name="Italian",
    defaults={"description": "Traditional Italian cuisine"}
)
mexican, _ = Category.objects.get_or_create(
    name="Mexican",
    defaults={"description": "Authentic Mexican dishes"}
)
dessert, _ = Category.objects.get_or_create(
    name="Dessert",
    defaults={"description": "Sweet treats"}
)
print("✅ Categories ready")

# Create ingredients
ingredients_data = [
    "Tomato", "Mozzarella Cheese", "Flour", "Eggs",
    "Olive Oil", "Garlic", "Basil", "Pasta",
    "Chocolate", "Sugar", "Butter", "Vanilla"
]

for ing_name in ingredients_data:
    Ingredient.objects.get_or_create(name=ing_name)
print("✅ Ingredients ready")

# ============================================
# STEP 3: CREATE Recipes
# ============================================

# Recipe 1: Margherita Pizza
recipe1, created = Recipe.objects.get_or_create(
    title="Margherita Pizza",
    defaults={
        "description": "Classic Italian pizza with fresh tomatoes, mozzarella, and basil",
        "author": user,
        "category": italian,
        "prep_time": 30,
        "cook_time": 15,
        "servings": 4,
        "difficulty": "easy",
        "instructions": """1. Prepare pizza dough and let it rise
2. Roll out dough into a circle
3. Spread tomato sauce
4. Add mozzarella cheese
5. Bake at 450°F for 12-15 minutes
6. Top with fresh basil leaves"""
    }
)
if created:
    # Add ingredients with quantities
    tomato = Ingredient.objects.get(name="Tomato")
    cheese = Ingredient.objects.get(name="Mozzarella Cheese")
    flour = Ingredient.objects.get(name="Flour")
    
    RecipeIngredient.objects.create(
        recipe=recipe1,
        ingredient=flour,
        quantity="2 cups",
        notes="All-purpose flour"
    )
    RecipeIngredient.objects.create(
        recipe=recipe1,
        ingredient=tomato,
        quantity="1 cup",
        notes="Crushed tomatoes"
    )
    RecipeIngredient.objects.create(
        recipe=recipe1,
        ingredient=cheese,
        quantity="200g",
        notes="Fresh mozzarella"
    )
    print(f"✅ Created: {recipe1.title}")

# Recipe 2: Chocolate Cake
recipe2, created = Recipe.objects.get_or_create(
    title="Chocolate Cake",
    defaults={
        "description": "Rich and moist chocolate cake perfect for celebrations",
        "author": user,
        "category": dessert,
        "prep_time": 20,
        "cook_time": 35,
        "servings": 8,
        "difficulty": "medium",
        "instructions": """1. Preheat oven to 350°F
2. Mix dry ingredients
3. Add wet ingredients
4. Pour into greased pan
5. Bake for 30-35 minutes
6. Let cool before frosting"""
    }
)
if created:
    chocolate = Ingredient.objects.get(name="Chocolate")
    sugar = Ingredient.objects.get(name="Sugar")
    flour = Ingredient.objects.get(name="Flour")
    eggs = Ingredient.objects.get(name="Eggs")
    
    RecipeIngredient.objects.create(recipe=recipe2, ingredient=chocolate, quantity="200g")
    RecipeIngredient.objects.create(recipe=recipe2, ingredient=sugar, quantity="1 cup")
    RecipeIngredient.objects.create(recipe=recipe2, ingredient=flour, quantity="1.5 cups")
    RecipeIngredient.objects.create(recipe=recipe2, ingredient=eggs, quantity="3 large")
    print(f"✅ Created: {recipe2.title}")

# Recipe 3: Pasta Carbonara
recipe3, created = Recipe.objects.get_or_create(
    title="Pasta Carbonara",
    defaults={
        "description": "Creamy Italian pasta with eggs, cheese, and pancetta",
        "author": user,
        "category": italian,
        "prep_time": 15,
        "cook_time": 20,
        "servings": 4,
        "difficulty": "medium",
        "instructions": """1. Cook pasta al dente
2. Fry pancetta until crispy
3. Mix eggs and cheese
4. Combine hot pasta with egg mixture
5. Add pancetta and black pepper
6. Serve immediately"""
    }
)
if created:
    pasta = Ingredient.objects.get(name="Pasta")
    eggs = Ingredient.objects.get(name="Eggs")
    cheese = Ingredient.objects.get(name="Mozzarella Cheese")
    
    RecipeIngredient.objects.create(recipe=recipe3, ingredient=pasta, quantity="400g")
    RecipeIngredient.objects.create(recipe=recipe3, ingredient=eggs, quantity="4 large")
    RecipeIngredient.objects.create(recipe=recipe3, ingredient=cheese, quantity="100g")
    print(f"✅ Created: {recipe3.title}")

print("\n" + "="*50)
print("✅ Sample data created!")
print("="*50 + "\n")

# ============================================
# STEP 4: QUERY Examples (Try these!)
# ============================================

print("📊 QUERY EXAMPLES:\n")

# 1. Get all recipes
print("1. All recipes:")
for recipe in Recipe.objects.all():
    print(f"   - {recipe.title} ({recipe.difficulty})")

# 2. Filter by difficulty
print("\n2. Easy recipes:")
easy = Recipe.objects.filter(difficulty="easy")
for recipe in easy:
    print(f"   - {recipe.title}")

# 3. Filter by category
print("\n3. Italian recipes:")
italian_recipes = Recipe.objects.filter(category__name="Italian")
for recipe in italian_recipes:
    print(f"   - {recipe.title}")

# 4. Filter with comparison
print("\n4. Recipes with prep_time >= 20 minutes:")
long_prep = Recipe.objects.filter(prep_time__gte=20)
for recipe in long_prep:
    print(f"   - {recipe.title}: {recipe.prep_time} min")

# 5. Search in title
print("\n5. Recipes containing 'Pizza':")
pizza_recipes = Recipe.objects.filter(title__icontains="Pizza")
for recipe in pizza_recipes:
    print(f"   - {recipe.title}")

# 6. Order by created date
print("\n6. Recipes ordered by newest:")
newest = Recipe.objects.order_by("-created_at")
for recipe in newest:
    print(f"   - {recipe.title} ({recipe.created_at})")

# 7. Get recipe with ingredients
print("\n7. Recipe ingredients:")
recipe = Recipe.objects.first()
if recipe:
    print(f"   Recipe: {recipe.title}")
    for ri in recipe.recipe_ingredients.all():
        print(f"   - {ri.quantity} {ri.ingredient.name}")

# 8. Count recipes
print("\n8. Statistics:")
total = Recipe.objects.count()
easy_count = Recipe.objects.filter(difficulty="easy").count()
print(f"   Total recipes: {total}")
print(f"   Easy recipes: {easy_count}")

# 9. Average prep time
print("\n9. Average prep time:")
avg_prep = Recipe.objects.aggregate(Avg("prep_time"))
print(f"   Average: {avg_prep['prep_time__avg']:.1f} minutes")

# 10. Recipes per category
print("\n10. Recipes per category:")
categories = Category.objects.annotate(recipe_count=Count("recipe_set"))
for cat in categories:
    print(f"   {cat.name}: {cat.recipe_count} recipes")

print("\n" + "="*50)
print("✅ Try modifying these queries!")
print("="*50)
