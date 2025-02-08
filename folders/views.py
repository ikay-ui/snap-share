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
import cloudinary.api
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
        form = UploadFileForm(user=request.user, data=request.POST, files=request.FILES)
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
                
            return redirect('photo_template:p_dashboard')
    else:
        form = UploadFileForm(user=request.user)

    context = {
        'form': form
    }
    return render(request, 'folders/upload.html', context)

@login_required
@photographer_required
def upload_zip(request):
    if request.method == 'POST':
        form = UploadZipForm(user=request.user, data=request.POST, files=request.FILES)
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
                return redirect('photo_template:p_dashboard')
                
            except CloudinaryError as e:
                messages.error(request, f'Error uploading ZIP file: {str(e)}')
            except Exception as e:
                messages.error(request, f'Unexpected error: {str(e)}')
    else:
        form = UploadZipForm(user=request.user)
        
    context = {
        'form': form
    }
    return render(request, 'folders/upload.html', context)



def get_folder_size(folder):
    """Calculate total size of folder including images and zip files"""

    # Get size of all images
    images = UploadFile.objects.filter(folder=folder)
    image_size = 0
    for image in images:
        try:
            # Get the Cloudinary URL for the image
            url = cloudinary_url(image.image.public_id)[0]
            # Make a HEAD request to get the content length
            response = requests.head(url)
            if 'content-length' in response.headers:
                image_size += int(response.headers['content-length'])
        except Exception as e:
            print(f"Error getting size for image {image.image.public_id}: {e}")
            continue

    # Get size of all zip files
    zip_files = UploadZip.objects.filter(folder=folder)
    zip_size = 0
    for zip_file in zip_files:
        try:
            # Get the Cloudinary URL for the zip file
            url = cloudinary_url(zip_file.zip_file.public_id)[0]
            # Make a HEAD request to get the content length
            response = requests.head(url)
            if 'content-length' in response.headers:
                zip_size += int(response.headers['content-length'])
        except Exception as e:
            print(f"Error getting size for zip file {zip_file.zip_file.public_id}: {e}")
            continue
    
    total_size = image_size + zip_size
    
    # Convert to appropriate unit
    if total_size < 1024:
        return f"{total_size}B"
    elif total_size < 1024**2:
        return f"{total_size/1024:.1f}KB"
    elif total_size < 1024**3:
        return f"{total_size/(1024**2):.1f}MB"
    return f"{total_size/(1024**3):.1f}GB"


@login_required
@photographer_required
def view_edit(request):
    if request.method == "POST":
        action = request.POST.get('action')
        folder_id = request.POST.get('folder_id')
        
        if not folder_id:
            return JsonResponse({'status': 'error', 'message': 'Folder ID required'})
            
        folder = get_object_or_404(Folder, id=folder_id)
        
        # Verify ownership
        if folder.owner != request.user:
            raise PermissionDenied
        
        if action == "edit":
            new_name = request.POST.get('name')
            new_description = request.POST.get('description')
            
            if new_name:
                folder.name = new_name
            if new_description:
                folder.description = new_description
                
            folder.save()
            messages.success(request, 'Folder updated successfully!')
            
        elif action == "delete":
            # Delete associated files from Cloudinary
            upload_files = UploadFile.objects.filter(folder=folder)
            for file in upload_files:
                if file.image:
                    cloudinary.uploader.destroy(file.image.public_id)
                    
            zip_files = UploadZip.objects.filter(folder=folder)
            for zip_file in zip_files:
                if zip_file.zip_file:
                    cloudinary.uploader.destroy(zip_file.zip_file.public_id)
                    
            folder.delete()
            messages.success(request, 'Folder deleted successfully!')
            
        return redirect('folders:view_edit')
    
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get all folders for the logged-in photographer with optional search
    folders = Folder.objects.filter(owner=request.user)
    if search_query:
        folders = folders.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    folders = folders.order_by('-created_at')
    
    # Prepare folder data with additional information
    folders_data = []
    for folder in folders:
        folder_data = {
            'id': folder.id,
            'name': folder.name,
            'created_at': folder.created_at,
            'description': folder.description,
            'total_files': (
                UploadFile.objects.filter(folder=folder).count() +
                UploadZip.objects.filter(folder=folder).count()
            ),
            'total_size': get_folder_size(folder)
        }
        folders_data.append(folder_data)
    
    context = {
        'folders': folders_data,
        'has_folders': bool(folders_data),
        'search_query': search_query
    }
    
    # If it's an AJAX request, return JSON response
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'html': render(request, 'folders/folder_list.html', context).content.decode(),
            'has_folders': bool(folders_data)
        })
    
    return render(request, 'folders/view_edit.html', context)

@login_required
@photographer_required
def view_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    
    # Verify ownership
    if folder.owner != request.user:
        raise PermissionDenied
    
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        image_id = request.POST.get('image_id')
        try:
            image = UploadFile.objects.get(id=image_id, folder=folder)
            # Delete from Cloudinary
            cloudinary.uploader.destroy(image.image.public_id)
            # Delete from database
            image.delete()
            return JsonResponse({'status': 'success', 'message': 'Image deleted successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    # Get all images for this folder
    images = UploadFile.objects.filter(folder=folder).order_by('-date_added')
    
    context = {
        'folder': folder,
        'images': images,
        'total_images': images.count()
    }
    return render(request, 'folders/view_folder.html', context)