from django.contrib import admin
from attendance.models import AttendanceRecord, CampusBoundary
# Register your models here.
admin.site.register(AttendanceRecord)
admin.site.register(CampusBoundary)
