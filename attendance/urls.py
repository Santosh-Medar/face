from django.urls import path
from attendance import views

urlpatterns = [
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('verify-location/', views.verify_location, name='verify_location'),
    path('face-recognition/', views.face_recognition_page, name='face_recognition_page'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/courses/', views.api_courses, name='api_courses'),
    path('api/courses/<str:course_name>/students/', views.api_course_students, name='api_course_students'),
]