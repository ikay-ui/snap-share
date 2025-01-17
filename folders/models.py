from django.db import models
from accounts.models import Account

from django.utils import timezone
from datetime import timedelta
import uuid
from cloudinary.models import CloudinaryField
from cloudinary.utils import cloudinary_url
# Create your models here.


class Folder(models.Model):
    # The name of the folder
    name = models.CharField(max_length=255)
    
    # A description for the folder, optional
    description = models.TextField(blank=True)

    # The owner of the folder, linking to the User model
    owner = models.ForeignKey(Account, on_delete=models.CASCADE)

    # A unique token generated for the folder, used for various purposes
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Counter for how many times the token has been used
    token_usage_count = models.PositiveIntegerField(default=0)

    # Timestamp for when the folder was created
    created_at = models.DateTimeField(auto_now_add=True)
    
    # adding expiry date for the token, set to 2days after creation
    expires_at = models.DateTimeField(default=timezone.now() + timedelta(days=2))

    # Property to check if the token is expired
    @property
    def is_token_expired(self):
        """
        Checks if the token has expired.
        The token is considered expired if it has been used more than 100 times
        or if the current time is past the expiry date.
        """
        return self.token_usage_count >= 100 or timezone.now() > self.expires_at

    # Method to increment the token usage count
    @property
    def increment_token_usage(self):
        """
        Increments the token usage count by 1 if the token is not expired.
        Saves the model instance after incrementing the count.
        """
        if not self.is_token_expired:
            self.token_usage_count += 1
            self.save()

    def __str__(self):
        return self.name
    
    
class UploadFile(models.Model):
    owner = models.ForeignKey(Account, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    image = CloudinaryField('image', 
                          folder='images_uploaded',  # This sets the folder in Cloudinary
                          resource_type='auto')      # Auto-detect resource type
    date_added = models.DateTimeField(auto_now_add=True)

    def get_image_url(self):
        """Return the proper Cloudinary URL for the image"""
        try:
            url, options = cloudinary_url(self.image.public_id,
                                        format=self.image.format,
                                        crop="fill",
                                        width=500,
                                        height=500)
            return url
        except Exception as e:
            print(f"Error generating Cloudinary URL: {e}")
            return None

    def __str__(self):
        return f"Image {self.id} in {self.folder.name}"
    
    # def __str__(self):
    #     return str(self.image)
    
class UploadZip(models.Model):
    owner = models.ForeignKey(Account, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    zip_file = CloudinaryField('zip_file',
                             folder='zip_files',    # This sets the folder in Cloudinary
                             resource_type='auto')  # Auto-detect resource type
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.zip_file)