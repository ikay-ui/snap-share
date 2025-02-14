from django.urls import path

from . import views

app_name = 'folders'


urlpatterns = [
    path('create_folder/', views.create_folder, name='create_folder'),
    
    # this is the upload thing-y happens
    path('upload_images/', views.upload_images, name='upload_images'),
    path('upload_file/', views.upload_file, name='upload_file'),
    path('upload_zip/', views.upload_zip, name='upload_zip'),
    path('view_edit_folder/', views.view_edit, name='view_edit'),
    path('view_folder/<int:folder_id>/', views.view_folder, name='view_folder'),
]