from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField

class LocationCategory(models.Model):
    name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(LocationCategory, on_delete=models.PROTECT)
    description = models.TextField(blank=True)
    coordinates = ArrayField(models.FloatField(), size=2)  # [longitude, latitude]
    is_common = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class UserFavoriteLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_locations'
    )
    location = models.ForeignKey(
        'Location',  # Reference to Location model
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'location')
        verbose_name = 'Favorite Location'
        verbose_name_plural = 'Favorite Locations'
    
    def __str__(self):
        return f"{self.user.username}'s favorite: {self.location.name}"