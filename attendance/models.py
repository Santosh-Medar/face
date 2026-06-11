from django.db import models
from accounts.models import StudentProfile
from django.db.models import JSONField

class CampusBoundary(models.Model):
    name = models.CharField(max_length=100, unique=True)
    boundary = models.JSONField(help_text="Store building boundary as list of [lon, lat] points", null=True, blank=True)  # store the exact campus shape
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class AttendanceRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    latitude = models.FloatField()
    longitude = models.FloatField()

    location_verified = models.BooleanField(default=False)
    face_verified = models.BooleanField(default=False)

    status = models.CharField(max_length=20, default='Pending')

    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.roll_no} - {self.date} - {self.status}"