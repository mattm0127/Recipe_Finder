from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.paginator import Paginator

from .forms import CustomUserCreationForm, IngredientInputForm
from . import models
from .extra_files.replacement_dictionary import replacements

import datetime
import requests
import random
from decouple import config
import json

# API Client
class SpoonacularClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = f'https://api.spoonacular.com'
    
    def _make_api_call(self, endpoint, params=None):
        """
        This function takes the endpoint and parameters for the API call,
        performs the API call and returns a json object with the recipes,
        returns a python dictionary with results.

        Args:
            endpoint: The API function to call.
            params: The parameters for the API call.
        """
        url = f'{self.base_url}{endpoint}'
        params = params or {}
        params['apiKey'] = self.api_key
        headers = {
            'Cache-Control': 'no-cache, no-store'
        }
        try:
            print(f"{params} sent to API")
            r = requests.get(url, params=params, headers=headers)
            r.raise_for_status()
            print(r.status_code)
            return r.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return True

    def _analyze_search_query(self, api_str):
        endpoint = '/recipes/queries/analyze'
        params = {
            'q': api_str,
        }
        response = self._make_api_call(endpoint=endpoint, params=params)
        query = ''
        ingredients = ''
        diet = ''

        for dish in response['dishes']:
            query += dish['name'].replace('-', ' ') + ','
        for ingredient in response['ingredients']:
            if ingredient['include'] == True:
                ingredients = ingredient['name'].replace('-', ' ') + ',' + ingredients
        for mod in response['modifiers']:
            diet += mod['name'].replace('_', ' ') + ','

        query += ingredients
        split_query = query.split(',')

        # Clean up anaylzed response to optimize complex response
        for x in range(len(split_query)):
            split_query[x] = replacements.get(split_query[x], split_query[x])

        query = ','.join(split_query)
        print(response)
        print(split_query)
        return query.strip(','), ingredients.strip(','), diet.strip(',')

    def get_recipes_by_complexSearch(self, api_str, num_results, offset=False):
        """
        This function takes a string of ingredients and the number of results
        desired, then makes a request to the spoonacular API to get a list of
        recipes that match the ingredients.

        Args:
            api_str: A string of ingredients separated by commas.
            result_num: The number of recipes to return.
        """
        query, ingredients, diet = self._analyze_search_query(api_str=api_str)
        random_offset = random.randrange(0, 10)
        endpoint = '/recipes/complexSearch'
        params = {
            'apiKey': config('API_KEY'),
            'query': api_str,
            'diet': diet,
            'includeIngredients': query,
            'instructionsRequired': True,
            'fillIngredients': True,
            'addRecipeInformation': True,
            'addRecipeInstructions': True,
            'ignorePantry': True,
            'number': num_results
            }
        if offset == True:
            params['offset'] =  random_offset

        return self._make_api_call(endpoint, params)
   
# Database Writer
  
# Functions
def get_recipes_by_ingredients(api_str, num_results, offset):
    """
    This function takes a string of ingredients and the number of results
    desired, then makes a request to the spoonacular API to get a list of
    recipes, ingredients and steps that match the ingredients.

    Args:
        api_str: A string of ingredients separated by commas.
        result_num: The number of recipes to return.
    """
    client = SpoonacularClient(api_key=config("API_KEY"))
    print('Client Initiated')
    return client.get_recipes_by_complexSearch(api_str=api_str, num_results=num_results, offset=offset)

def add_recipe_to_database(api_response, user, user_recipes_list):
    """
    This function takes an API response and a user object, then adds the
    recipes from the API response to the database if the API_ID is not currently
    in the Users recipes.

    Args:
        api_response: The API response from the spoonacular API.
        user: The user object.
    """
    for recipe in api_response['results']:
        if recipe['id'] in user_recipes_list:
            print(f"Recipe {recipe['id']} already in Users database")
            continue
        new_recipe = models.UserRecipe()
        new_recipe.user_id = user
        new_recipe.api_id = recipe['id']
        new_recipe.name = recipe['title']
        new_recipe.image = recipe['image']
        new_recipe.save()    
        print(f"Recipe {recipe['id']} added to User.")  
    return None

def add_recipe_information_to_database(api_response, api_id):
    for recipe in api_response['results']:
        if api_id == recipe['id']:
            recipe_info = models.RecipeInformation()
            recipe_info.recipe_api_id = recipe['id']
            recipe_info.title = recipe['title']
            recipe_info.image = recipe['image']
            recipe_info.ready_in_minutes = recipe['readyInMinutes']
            recipe_info.preparation_min = recipe['preparationMinutes']
            recipe_info.cook_min = recipe['cookingMinutes']
            recipe_info.servings = recipe['servings']
            recipe_info.summary = recipe['summary']
            recipe_info.weight_watchers_points = recipe['weightWatcherSmartPoints']
            recipe_info.vegetarian = recipe['vegetarian']
            recipe_info.vegan = recipe['vegan']
            recipe_info.gluten_free = recipe['glutenFree']
            recipe_info.dairy_free = recipe['dairyFree']
            recipe_info.low_fodmap = recipe['lowFodmap']
            recipe_info.source_name = recipe['sourceName']
            recipe_info.source_url = recipe['sourceUrl']
            recipe_info.save()
    return None

def add_ingredients_to_database(api_response, api_id):
    """
    This function takes an API response and an API ID, then adds the
    ingredients from the API response to the database.

    Args:
        api_response: The API response from the spoonacular API.
        api_id: The API ID of the recipe.
    """
    for recipe in api_response['results']:
        if api_id == recipe['id']:
            for ingredient in recipe['extendedIngredients']:
                ingred = models.Ingredient()
                ingred.recipe_api_id = recipe['id']
                ingred.name = ingredient['name']
                ingred.amount = ingredient['amount']
                ingred.info = ingredient['original']
                ingred.unit = ingredient['unit']
                ingred.save()
    return None

def add_procedure_to_database(api_response, api_id):
    """
    This function takes an API response and an API ID, then adds the
    procedure from the API response to the database.

    Args:
        api_response: The API response from the spoonacular API.
        api_id: The API ID of the recipe.
    """
    for recipe in api_response['results']:
        if api_id == recipe['id']:
            for section in recipe['analyzedInstructions']:
                for step in section['steps']:
                    proced = models.Procedure()
                    proced.recipe_api_id = recipe['id']
                    proced.step_number = step['number']
                    proced.step = step['step']
                    proced.save()
    return None

def process_database_request(api_response, user):
    """
    This function takes a recipe object and an API ID, then processes the
    final request to the spoonacular API to get the full recipe information.

    Args:
        api_response: The API response object.
        user: The User ID for the request.
    """
    user_recipes = models.UserRecipe.objects.filter(user_id=user).values('api_id')
    user_recipes_list = [recipe['api_id'] for recipe in user_recipes]
    recipes = models.Ingredient.objects.values('recipe_api_id')
    recipe_set = list(set([recipes[x]['recipe_api_id'] for x in range(len(recipes))]))
    
    # Try to get api id list, if NoneType return Error
    try:
        api_id_list = [recipe['id'] for recipe in api_response['results']]
    except:
        return True

    # Check for Length of api recipe ids, if empty return Error
    if len(api_id_list) == 0:
        print('Nothing was returned from API.')
        return True
    
    # Add the recipe to the UserRecipe Table if not already added.
    add_recipe_to_database(api_response=api_response, user=user, user_recipes_list=user_recipes_list)
    
    # Check to see if api_id is already in RecipeInformation, otherwise adds info, ingredients, procedure
    try:
        for api_id in api_id_list:
            if api_id in recipe_set:
                print(f'API_ID: {api_id} is already added, skipping')
                continue
            print(f'Adding {api_id} info, ingredients and procedure to database')
            add_recipe_information_to_database(api_response=api_response, api_id=api_id)
            add_ingredients_to_database(api_response=api_response, api_id=api_id)
            add_procedure_to_database(api_response=api_response, api_id=api_id)
        print('Recipes Added to the Database')
        return api_id_list
    except Exception as e:
        print(f'Error: {e}')
        return True
    
def get_full_recipe(api_id, user):
    """
    This function takes a recipe object and an API ID, then retrieves the
    full recipe information from the database.

    Args:
        recipe: The recipe object.
        api_id: The API ID of the recipe.
    """
    recipe_info = models.RecipeInformation.objects.get(recipe_api_id=api_id)
    ingredient_list = models.Ingredient.objects.filter(recipe_api_id=api_id).values()
    procedure_list = models.Procedure.objects.filter(recipe_api_id=api_id).values()
    user_recipe_info = models.UserRecipe.objects.get(user_id=user, api_id=api_id)

    split_summary = recipe_info.summary.split('.')
    filtered_summary = [x for x in split_summary if '<a href=' not in x and 'com/' not in x]
    summary = '. '.join(filtered_summary)
    recipe_info.summary = summary

    context = {}
    context['recipe_info'] = recipe_info
    context['ingredients'] = [{
        'name': ingredient['name'],
        'amount': ingredient['amount'],
        'info': ingredient['info'],
        'unit': ingredient['unit']
        } for ingredient in ingredient_list]
    context['procedure'] = [{
        'step_number': procedure['step_number'],
        'step': procedure['step']
        } for procedure in procedure_list]
    context['user_info'] = user_recipe_info
    return context

# Views
class SignUp(CreateView):
    """View to handle user sign-up."""
    """Create a new user form."""
    form_class = CustomUserCreationForm
    template_name = "registration/signup.html"
    def form_valid(self, form):
        form.save()
        return redirect('home')

class Account(LoginRequiredMixin, ListView):
    model = User
    template_name = 'recipe_app/account_info.html'

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(username=user).values()

class AccountUpdate(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = 'recipe_app/account_update.html'
    success_url = '/account/'

@login_required
def home(request):
    """View to render the home page."""
    user = request.user
    recent_recipes = models.UserRecipe.objects.filter(user_id=user)

    if len(recent_recipes) == 0:
        context = {'recent_recipes': 'Search Recipes by Your Ingredients!',
                   'empty': True}
    else:
        viewed_recipes = recent_recipes.filter(was_selected=True).order_by('-date_searched')
        skipped_recipes = recent_recipes.filter(was_selected=False).order_by('-date_searched')[:50]
        context = {'viewed_recipes': viewed_recipes,
                   'skipped_recipes': skipped_recipes,
                   'empty': False}
    return render(request, 'recipe_app/home.html', context=context)

@login_required
def get_recipes_view(request):
    """View to handle user ingredient input and recipe search."""
    if request.method == 'POST':
        print('Ingredient Form Received')
        form = IngredientInputForm(request.POST)
        if form.is_valid():
            user = request.user
            num_results = 6
            attempts = 0
            api_string = str(form.cleaned_data['ingredients']).lower().replace('chop meat', 'ground beef')
            offset = False

            while attempts < 3:
                print(f"API Call attempt: {attempts}")
                api_response = get_recipes_by_ingredients(api_str=api_string, num_results=num_results, offset=offset)
                error_or_api_ids = process_database_request(api_response=api_response, user=user)
                attempts += 1
                if error_or_api_ids == True and len(api_string) >= 8 and attempts < 2:
                    api_string = api_string[:-5]
                elif error_or_api_ids == True and len(api_string) < 8:
                    api_string = ''
                    offset = True
                elif error_or_api_ids == True and attempts == 2:
                    api_string = ''
                    offset = True
                else:
                    break
            
            if error_or_api_ids == True:
                form = IngredientInputForm()
                return render(request, 'recipe_app/get_ingredients_error.html', {'form': form})
            
            if len(api_string) == 0:
                title = "Hmm, Nothing With that Combo. Maybe One of These?"
            else:
                title = "Here Are Your Potential Dinners"

            object_list = models.UserRecipe.objects.filter(user_id=user, api_id__in=error_or_api_ids)
            summary_list = models.RecipeInformation.objects.filter(recipe_api_id__in=error_or_api_ids).values('recipe_api_id', 'summary')
            for summary in summary_list:
                split_summary = summary['summary'].split('.')
                summary['summary'] = '. '.join(split_summary[:-5]) + '.'
            context = {
                'object_list': object_list,
                'title': title,
                'summary_list': summary_list
            }
            return render(request, 'recipe_app/recipe_choice.html', context=context)
    form = IngredientInputForm()
    return render(request, 'recipe_app/get_ingredients.html', {'form': form})

@login_required
def load_recipe_view(request, api_id):
    """View to enter, load and display a selected recipe to and from the databse."""
    user = request.user
    try:
        recipe = models.UserRecipe.objects.get(user_id=user, api_id=api_id)
        recipe.was_selected = True
        recipe.date_searched = datetime.datetime.now(tz=None)
    except:
        recipe_info = models.RecipeInformation.objects.get(recipe_api_id=api_id)
        recipe = models.UserRecipe()
        recipe.user_id = user
        recipe.api_id = recipe_info.recipe_api_id
        recipe.name = recipe_info.title
        recipe.image=recipe_info.image
        recipe.was_selected = True
        recipe.date_searched = datetime.datetime.now(tz=None)
    recipe.save()

    context = get_full_recipe(api_id, user)
    return render(request, 'recipe_app/show_recipe.html', context=context)

@login_required
def all_recents_view(request, recipe_filter):
    user = request.user
    match recipe_filter:
        case 'recents':
            recent_recipes = models.UserRecipe.objects.filter(user_id=user, was_selected=True).order_by('-date_searched')
        case 'skipped':
            recent_recipes = models.UserRecipe.objects.filter(user_id=user, was_selected=False).order_by('-date_searched')[:50]
        case 'favorites':
            recent_recipes = models.UserRecipe.objects.filter(user_id=user, is_favorite=True).order_by('-date_searched')

    paginator = Paginator(recent_recipes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'recipe_filter': recipe_filter,
        'page_obj': page_obj
    }
    return render(request, 'recipe_app/recent_recipes.html', context=context)

@login_required
def favorite_recipe(request, api_id, favorite_bool):
    user = request.user
    if favorite_bool == 'True':
        models.UserRecipe.objects.filter(user_id=user, api_id=api_id).update(is_favorite=True)
    if favorite_bool == 'False':
        models.UserRecipe.objects.filter(user_id=user, api_id=api_id).update(is_favorite=False)
    return redirect('load_recipe', api_id=api_id)

@login_required
def delete_recipe(request, recipe_id):
    return None

@login_required
def logout_request(request): 
    """View to handle user logout."""
    logout(request)
    return redirect('login')
