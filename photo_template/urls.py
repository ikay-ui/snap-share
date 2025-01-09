from django.urls import path

from . import views

app_name  = 'photo_template'


urlpatterns = [
    path('', views.index, name='index'),
    path('selection/', views.selection, name='selection'),
    path('photographer_dashboard/', views.p_dashboard, name='p_dashboard'),
    path('client_dashboard/', views.c_dashboard, name='c_dashboard'),
    path('search_token/', views.search_token, name='search_token'),
    path('search/', views.searched_folder, name='searched_folder'),

    path('view_all/<int:folder_id>/view/', views.view_all, name='view_all'),
    path('folder/<int:folder_id>/download-all/', views.download_all, name='download_all'),

    # this is for adding folder into my favorites
    path('toggle-favorite/<int:folder_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('my_favorites/', views.my_favorites, name='my_favorites'),
    path('contact_support/', views.contact_support, name='contact_support'),

]