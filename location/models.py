from django.db import models
from django.conf import settings

class LocationCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon_class = models.CharField(max_length=50)  # FontAwesome icon
    
    class Meta:
        app_label = 'location'
        verbose_name = 'Location Category'
        verbose_name_plural = 'Location Categories'
    
    def __str__(self):
        return self.name

class CampusLocation(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16)
    latitude = models.DecimalField(max_digits=22, decimal_places=16)
    category = models.ForeignKey(
        LocationCategory, 
        on_delete=models.PROTECT,
        related_name='locations'
    )
    floor_level = models.IntegerField(default=0)
    is_accessible = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_locations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'location'
        ordering = ['name']
        indexes = [
            models.Index(fields=['longitude', 'latitude']),
        ]
        verbose_name = 'Campus Location'
        verbose_name_plural = 'Campus Locations'
        
    def __str__(self):
        return f"{self.name} ({self.category})"

class UserFavoriteLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_locations'
    )
    location = models.ForeignKey(
        CampusLocation,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'location'
        unique_together = [['user', 'location']]
        verbose_name = 'User Favorite Location'
        verbose_name_plural = 'User Favorite Locations'

    def __str__(self):
        return f"{self.user}'s favorite: {self.location}"