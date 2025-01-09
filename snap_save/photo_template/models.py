from django.db import models
from accounts.models import Account
from folders.models import Folder
from django.core.mail import send_mail
from django.conf import settings
# Create your models here.

class FavoriteFolder(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'folder') #it prevents adding duplicate folders
        ordering = ['-added_at'] # most recent first



class SupportTicket(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progess', 'In Progess'),
        ('resolved', 'Resolved'),
    ]

    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)


        if is_new:
            # send email notification to admin
            send_mail(
                f'New Support Ticket: {self.subject}',
                f'New support ticket from {self.user.email}:\n\nPriority: {self.priority}\n\n{self.message}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=True,
            )