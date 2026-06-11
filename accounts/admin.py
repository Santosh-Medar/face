from django.contrib import admin
from .models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('roll_no', 'user', 'course', 'semester', 'phone')
    search_fields = ('roll_no', 'user__username', 'course')