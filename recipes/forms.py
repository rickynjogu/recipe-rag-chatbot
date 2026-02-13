from django import forms
from .models import Recipe, Review, RecipeIngredient, Ingredient


class RecipeForm(forms.ModelForm):
    """Form for creating/editing recipes"""
    
    class Meta:
        model = Recipe
        fields = [
            "title",
            "description",
            "category",
            "prep_time",
            "cook_time",
            "servings",
            "difficulty",
            "instructions",
            "image",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Recipe Title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "prep_time": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "cook_time": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "servings": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "difficulty": forms.Select(attrs={"class": "form-control"}),
            "instructions": forms.Textarea(attrs={"class": "form-control", "rows": 10}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }


class ReviewForm(forms.ModelForm):
    """Form for submitting reviews"""
    
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "max": 5,
                "type": "range",
            }),
            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Write your review here..."
            }),
        }
