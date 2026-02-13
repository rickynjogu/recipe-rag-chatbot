from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect("recipes:recipe_list")
    
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}! 👋")
            next_url = request.GET.get("next", "recipes:recipe_list")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    
    return render(request, "accounts/login.html")


class RegisterView(CreateView):
    """User registration view"""
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("recipes:recipe_list")
    
    def form_valid(self, form):
        messages.success(self.request, "Account created successfully! Welcome to RecipeAI! 🎉")
        response = super().form_valid(form)
        # Auto-login after registration
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        user = authenticate(username=username, password=password)
        if user:
            login(self.request, user)
        return response
