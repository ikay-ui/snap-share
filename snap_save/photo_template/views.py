from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .decorators import photographer_required, client_required
from django.contrib import messages

from folders.models import Folder
from .forms import SupportTicketForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import FavoriteFolder
# this is when pictures are actually converted in to zip files for downloading
import os
import zipfile
from django.http import HttpResponse
from io import BytesIO
# Create your views here.


def index(request):
    return render(request, 'photo_template/index.html')


def selection(request):
    return render(request, 'photo_template/selection.html')


@login_required
@photographer_required
def p_dashboard(request):
    return render(request, 'photo_template/p_dashboard.html')


@login_required
@client_required
def c_dashboard(request):
    return render(request, 'photo_template/c_dashboard.html')

def search_token(request):
    return render(request, 'photo_template/search_token.html')

def searched_folder(request):
    if request.method == 'POST':
    # we now check if the request if it is a post request.
        token = request.POST.get('token')
        # getting the value that is in the name attribute
        try:
            folder = Folder.objects.get(token__exact=token)
            # the moment the user inserts the token, we update the trial field in the database
            folder.increment_token_usage
            
            # check if the token is expired after incrementing
            if folder.is_token_expired:
                messages.error(request, 'The token has expired.')
                return redirect('photo_template:c_dashboard')
            else:
                # render the search results
                context = {
                    'folder': folder,
                }
            return render(request, 'photo_template/searched_folder.html', context)
        except Folder.DoesNotExist:
            messages.error(request, 'Invalid token. Please try again.')
            return redirect('photo_template:c_dashboard')
    else:
        return render(request, 'photo_template/searched_folder.html')

def view_all(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)

    context = {
        'folder':folder,
    }
    return render(request, 'photo_template/view_all.html', context)

def download_all(request, folder_id):
    # get the folder or return 404 status
    folder = get_object_or_404(Folder, id=folder_id)

    # create a BytesIO buffer to store the zip file
    buffer = BytesIO()

     # Create the zip file
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add all images from UploadFile
        for upload in folder.uploadfile_set.all():
            file_path = upload.image.path
            arc_name = os.path.basename(file_path)
            zip_file.write(file_path, arc_name)
            
        # Add all ZIP files from UploadZip
        for zip_upload in folder.uploadzip_set.all():
            file_path = zip_upload.zip_file.path
            arc_name = os.path.basename(file_path)
            zip_file.write(file_path, arc_name)
    
    # Prepare response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{folder.name}_all_files.zip"'
    
    return response

@login_required
@require_POST
def toggle_favorite(request, folder_id):
    try:
        folder = get_object_or_404(Folder, id=folder_id)
        favorite = FavoriteFolder.objects.filter(user=request.user, folder=folder)
        
        if favorite.exists():
            favorite.delete()
            return JsonResponse({'status': 'removed'})
        else:
            FavoriteFolder.objects.create(user=request.user, folder=folder)
            return JsonResponse({'status': 'added'})
    except Exception as e:
        
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@client_required
def my_favorites(request):
    favorites = FavoriteFolder.objects.filter(
        user=request.user
    )
    context = {
        'favorites':favorites
    }
    return render(request, 'photo_template/my_favorites.html', context)

@login_required
@client_required
def contact_support(request):
    if request.method == "POST":
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            messages.success(request, 'Your support ticket has been submitted successfully. We\'ll get back to you soon!')
            return redirect('photo_template:c_dashboard')
    else:
        form = SupportTicketForm()

    return render(request, 'photo_template/contact_support.html', {'form': form})
