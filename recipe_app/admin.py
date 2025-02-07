from django.contrib import admin
from . import models

admin.site.register(models.UserRecipe)
admin.site.register(models.RecipeInformation)
admin.site.register(models.Ingredient)
admin.site.register(models.Procedure)
