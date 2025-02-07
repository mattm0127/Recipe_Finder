from django.db import models
from django.contrib.auth.models import User

class UserRecipe(models.Model):
    """
    UserRecipe model
    user_id: Foreign key to the User model
    api_id: Integer representing the recipe's ID from the external API
    image: URL to image file for recipe
    was_selected: Boolean indicating whether the recipe was selected by the user
    """
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    api_id = models.IntegerField(blank=False, null=False)
    name = models.CharField(max_length=50) 
    image = models.CharField(max_length=150) # Same as above
    was_selected = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    date_searched = models.DateTimeField(auto_now=True, blank=False, null=False)

    def __str__(self):
        return f"{self.user_id}: {self.name}"

class RecipeInformation(models.Model):
    """
    RecipeInformation model
    Adds all of the recipe specific information.
    """
    recipe_api_id = models.IntegerField(blank=False, null=False)
    title = models.CharField(max_length=50)
    image = models.CharField(max_length=150)
    ready_in_minutes = models.IntegerField(blank=True, null=True)
    preparation_min = models.IntegerField(blank=True, null=True)
    cook_min = models.IntegerField(blank=True, null=True)
    servings = models.IntegerField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    weight_watchers_points = models.IntegerField(blank=True, null=True)
    vegetarian = models.BooleanField(default=False)
    vegan = models.BooleanField(default=False)
    gluten_free = models.BooleanField(default=False)
    dairy_free = models.BooleanField(default=False)
    low_fodmap = models.BooleanField(default=False)
    source_name = models.CharField(max_length=50)
    source_url = models.URLField(max_length=150)

    def __str__(self):
        return self.title

class Ingredient(models.Model):
    """
    Ingredient model
    recipe_api_id: Integer representing the recipe's ID from the external API
    name: CharField for the ingredient's name
    amount: Integer for the quantity of the ingredient
    info: Detailed information about the amount
    unit: CharField for the unit of measurement
    """
    recipe_api_id = models.IntegerField(blank=False, null=False)
    name  = models.CharField(max_length=50)
    amount = models.IntegerField(blank=False, null=False)
    info = models.CharField(max_length=50)
    unit = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.name} ({UserRecipe.objects.get(api_id=self.recipe_api_id).name})"

class Procedure(models.Model):
    """
    Procedure model
    recipe_api_id: Integer representing the recipe's ID from the external API
    step_number: Integer representing the step number in the recipe
    step: TextField for the description of the step
    """
    recipe_api_id = models.IntegerField(blank=False, null=False)
    step_number = models.IntegerField(blank=False, null = False)
    step = models.TextField()

    def __str__(self):
        return f"{UserRecipe.objects.get(api_id=self.recipe_api_id).name}: Step {self.step_number}"
