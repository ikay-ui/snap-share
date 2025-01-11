from django.shortcuts import render, redirect, get_object_or_404

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Folder, UploadFile, UploadZip
from django.db.models import Q
from .forms import FolderCreationForm, UploadFileForm, UploadZipForm
from photo_template.decorators import photographer_required
from .reused_func import send_token


from django.core.exceptions import PermissionDenied
import cloudinary
from cloudinary.utils import cloudinary_url
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
import requests
from django.http import JsonResponse


# Create your views here.


@login_required
@photographer_required
def create_folder(request):
    # to get rid of the not null constraint, we need to set the owner field to the logged in user
    user = request.user
    token = None
    # for one to create a folder, we need to check whether if the request is a get or post request
    if request.method != 'POST':
        # send out the form again as it is not a POST request
        form = FolderCreationForm()
    else:
        # accept the form with the data that it has been submitted with
        form = FolderCreationForm(request.POST)
        # print(form)
        # now we need to check to see if the form is valid
        if form.is_valid():
            # use the try-except block
            try:
                # now, we get the the two fields and save them in variables
                name = form.cleaned_data['name']
                # this here is written like this because, in case a user intentionally left the field empty, a default string is provided which won't cause error
                description = form.cleaned_data.get('description', '')
                # now after this, we call the folder class to make an instance of it
                folder = Folder.objects.create(name=name,owner=user, description=description)
                folder.save()
                token = folder.token  # Get the generated token for the folder
                
                # send a token to the user email
                send_token(request, user.email, token)
                # send a message to the user notifying them that a token has been generated for them for that specific folder
                messages.success(request, f'A token for {folder.name} has been generated for you. Please check your email')
                # Pass the token to the context
                context = {
                    'form': FolderCreationForm(),
                    'token': token
                }
                return render(request, 'folders/create_folder.html', context)
            except Exception as e:
                print(e)
    context = {
        'form':form,
        'token':token
    }
    return render(request, 'folders/create_folder.html', context)


@login_required
@photographer_required
def upload_images(request):
    return render(request, 'folders/upload_images.html')


@login_required
@photographer_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            folder = form.cleaned_data['folder']
            files = request.FILES.getlist('images')
            
            success_count = 0
            error_count = 0
            
            for file in files:
                try:
                    # Create the upload file instance
                    upload = UploadFile(
                        owner=request.user,
                        folder=folder
                    )
                    
                    # Explicitly handle the Cloudinary upload
                    upload_result = cloudinary.uploader.upload(
                        file,
                        folder=f'images_uploaded/{folder.id}',
                        resource_type='auto'
                    )
                    
                    # Assign the Cloudinary resource to the model
                    upload.image = upload_result['public_id']
                    upload.save()
                    
                    success_count += 1
                    
                except CloudinaryError as e:
                    error_count += 1
                    messages.error(request, f'Error uploading {file.name}: {str(e)}')
                except Exception as e:
                    error_count += 1
                    messages.error(request, f'Unexpected error uploading {file.name}: {str(e)}')
            
            if success_count > 0:
                messages.success(request, f'Successfully uploaded {success_count} files')
            if error_count > 0:
                messages.warning(request, f'Failed to upload {error_count} files')
                
            return redirect('folders:p_dashboard')
    else:
        form = UploadFileForm()

    context = {
        'form': form
    }
    return render(request, 'folders/upload.html', context)

@login_required
@photographer_required
def upload_zip(request):
    if request.method == 'POST':
        form = UploadZipForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create but don't save the instance yet
                zip_instance = form.save(commit=False)
                zip_instance.owner = request.user
                
                # Explicitly handle Cloudinary upload
                upload_result = cloudinary.uploader.upload(
                    request.FILES['zip_file'],
                    folder=f'zip_files/{zip_instance.folder.id}',
                    resource_type='auto'
                )
                
                # Assign the Cloudinary resource
                zip_instance.zip_file = upload_result['public_id']
                zip_instance.save()
                
                messages.success(request, 'ZIP file uploaded successfully')
                return redirect('folders:p_dashboard')
                
            except CloudinaryError as e:
                messages.error(request, f'Error uploading ZIP file: {str(e)}')
            except Exception as e:
                messages.error(request, f'Unexpected error: {str(e)}')
    else:
        form = UploadZipForm()
        
    context = {
        'form': form
    }
    return render(request, 'folders/upload.html', context)