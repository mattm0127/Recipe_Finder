from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')), # contains name='login'
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('logout/', views.logout_request, name='logout'),
    path('account/', views.Account.as_view(), name='account'),
    path('account/<int:pk>/update/', views.AccountUpdate.as_view(), name='update_account'),
    path('', views.home, name='home'),
    path('recent-recipes/<str:recipe_filter>/', views.all_recents_view, name='recent_recipes'),
    path('get-recipes/', views.get_recipes_view, name='get_recipes'),
    path('get-recipes/recipe-choice/<int:api_id>/', views.load_recipe_view, name='load_recipe'),
    path('get-recipes/recipe-choice/<int:api_id>/<str:favorite_bool>', views.favorite_recipe, name='favorite'),

]