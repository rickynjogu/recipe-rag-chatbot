from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from .models import Recipe, Category, Review
from .forms import RecipeForm, ReviewForm


class RecipeListView(ListView):
    """Display list of all recipes"""
    model = Recipe
    template_name = "recipes/recipe_list.html"
    context_object_name = "recipes"
    paginate_by = 12

    def get_queryset(self):
        queryset = Recipe.objects.select_related("author", "category").prefetch_related("reviews")
        category = self.request.GET.get("category")
        difficulty = self.request.GET.get("difficulty")
        
        if category:
            queryset = queryset.filter(category_id=category)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class RecipeDetailView(DetailView):
    """Display single recipe details"""
    model = Recipe
    template_name = "recipes/recipe_detail.html"
    context_object_name = "recipe"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recipe = self.get_object()
        
        # Check if user has already reviewed
        user_review = None
        if self.request.user.is_authenticated:
            user_review = Review.objects.filter(recipe=recipe, user=self.request.user).first()
        
        context["user_review"] = user_review
        context["reviews"] = recipe.reviews.select_related("user").order_by("-created_at")[:10]
        context["review_form"] = ReviewForm()
        
        # Similar recipes (same category)
        if recipe.category:
            context["similar_recipes"] = Recipe.objects.filter(
                category=recipe.category
            ).exclude(pk=recipe.pk)[:4]
        
        return context

    def post(self, request, *args, **kwargs):
        """Handle review submission"""
        recipe = self.get_object()
        
        if not request.user.is_authenticated:
            from django.contrib import messages
            messages.warning(request, "Please log in to submit a review.")
            return redirect("accounts:login")
        
        form = ReviewForm(request.POST)
        
        if form.is_valid():
            review, created = Review.objects.get_or_create(
                recipe=recipe,
                user=request.user,
                defaults=form.cleaned_data
            )
            if not created:
                # Update existing review
                review.rating = form.cleaned_data["rating"]
                review.comment = form.cleaned_data["comment"]
                review.save()
            from django.contrib import messages
            messages.success(request, "Review submitted successfully!")
        
        return redirect("recipes:recipe_detail", pk=recipe.pk)


class RecipeCreateView(LoginRequiredMixin, CreateView):
    """Create a new recipe"""
    model = Recipe
    form_class = RecipeForm
    template_name = "recipes/recipe_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class RecipeUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing recipe"""
    model = Recipe
    form_class = RecipeForm
    template_name = "recipes/recipe_form.html"

    def get_queryset(self):
        # Users can only edit their own recipes
        return Recipe.objects.filter(author=self.request.user)


class RecipeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a recipe"""
    model = Recipe
    template_name = "recipes/recipe_confirm_delete.html"
    success_url = "/"

    def get_queryset(self):
        # Users can only delete their own recipes
        return Recipe.objects.filter(author=self.request.user)


class CategoryDetailView(DetailView):
    """Display recipes in a category"""
    model = Category
    template_name = "recipes/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recipes"] = Recipe.objects.filter(category=self.get_object())
        return context


class RecipeSearchView(ListView):
    """Search recipes"""
    model = Recipe
    template_name = "recipes/recipe_list.html"
    context_object_name = "recipes"
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get("q", "")
        if query:
            return Recipe.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(instructions__icontains=query) |
                Q(ingredients__name__icontains=query)
            ).distinct()
        return Recipe.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context
