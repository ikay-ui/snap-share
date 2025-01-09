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
            files = form.cleaned_data['images']

            for file in files:
                UploadFile.objects.create(owner=request.user, folder=folder, image=file)

            # return JsonResponse({'success': True})  # Return JSON response
            return redirect('folders:p_dashboard')
        else:
            return redirect('folders:upload_file')
    else:
        form = UploadFileForm()

    context = {
        'form': form
    }
    return render(request, 'folders/upload.html', context)


@login_required
@photographer_required
def upload_zip(request):
    if request.method != 'POST':
        # return the form back to the user
        form = UploadZipForm()
    
    else:
        form = UploadZipForm(request.POST, request.FILES) #Initializing the form with the POST data and uploaded
        # checking if the form is valid
        if form.is_valid():
            try:
                zip_instance = form.save(commit=False) #saving the form but not committing to the database yet
                zip_instance.owner = request.user # Setting the owner of the ZIP file to the current user
                zip_instance.save() # Saving the ZIP file instance to the database
                
                return redirect('folders:upload_zip')
            except:
                pass
    context = {
        'form':form
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
            new_price = request.POST.get('price')
            
            if new_name:
                folder.name = new_name
            if new_description:
                folder.description = new_description
            if new_price:
                folder.price = new_price
                
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