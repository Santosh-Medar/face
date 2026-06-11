from django.db import models
from django.contrib.auth.models import User

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_no = models.CharField(max_length=20, unique=True)
    course = models.CharField(max_length=50)
    semester = models.CharField(max_length=20)
    phone = models.CharField(max_length=15, blank=True, null=True)

    # Face recognition data will be stored later
    face_image = models.ImageField(upload_to='student_faces/', blank=True, null=True)
    face_encoding = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.roll_no} - {self.user.username}"
    