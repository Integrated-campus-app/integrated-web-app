from django.db import models

class Building(models.Model):
    name = models.CharField(max_length=100, unique=True, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    CATEGORY_CHOICES = [
        ('ENTRANCE', 'Entrance'),
        ('LOUNGE', 'Lounge'),
        ('CAFE', 'Cafe'),
        ('COURT', 'Court'),
        ('STADIUM', 'Stadium'),
        ('AMPHI', 'Amphitheater'),
        ('SCHOOL', 'School'),
        ('DEPARTMENT', 'Department'),
        ('LAB', 'Lab'),
        ('STEM', 'STEM Center'),
        ('CLASSROOM', 'Classroom'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)  # Changed from 'type' to 'category'
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"