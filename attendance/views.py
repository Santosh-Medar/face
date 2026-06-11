import json
import logging
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from shapely.geometry import Point, Polygon
from .models import CampusBoundary
from accounts.models import StudentProfile

logger = logging.getLogger(__name__)


@login_required
def student_dashboard(request):
    return render(request, 'attendance/student_dashboard.html')


@login_required
def verify_location(request):
    """Verify if student's GPS location is inside the active campus boundary using polygon.
    Does NOT create an attendance record – only returns location verification result."""
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method. Use POST.'
        }, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON body.'
        }, status=400)

    # Extract and validate coordinates
    try:
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        print(f"Received coordinates: {latitude}, {longitude}")
    except (TypeError, ValueError):
        return JsonResponse({
            'status': 'error',
            'message': 'Latitude and longitude must be valid numbers.'
        }, status=400)

    # Basic coordinate range check
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return JsonResponse({
            'status': 'error',
            'message': 'Coordinates out of valid range.'
        }, status=400)

    # Get active campus boundary with polygon
    boundary = CampusBoundary.objects.filter(is_active=True).first()
    if not boundary:
        logger.warning("No active campus boundary configured.")
        return JsonResponse({
            'status': 'error',
            'message': 'Campus boundary is not configured. Please contact administrator.'
        }, status=503)

    # Validate boundary polygon
    if not boundary.boundary or not isinstance(boundary.boundary, list) or len(boundary.boundary) < 3:
        logger.error("Boundary polygon is missing or invalid (needs at least 3 points).")
        return JsonResponse({
            'status': 'error',
            'message': 'Campus boundary polygon is not properly configured.'
        }, status=500)

    # Build closed polygon
    polygon_coords = boundary.boundary
    if polygon_coords[0] != polygon_coords[-1]:
        polygon_coords = polygon_coords + [polygon_coords[0]]
    
    try:
        campus_polygon = Polygon(polygon_coords)
    except Exception as e:
        logger.error(f"Failed to create polygon from boundary: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid campus polygon coordinates.'
        }, status=500)

    # Student's current location
    student_point = Point(longitude, latitude)

    # Add buffer for GPS accuracy (approx 16 meters)
    buffered_polygon = campus_polygon.buffer(0.00015)
    is_inside = buffered_polygon.contains(student_point)

    # Return result – no attendance record is created
    if is_inside:
        request.session['location_verified'] = True
        request.session.save()
        return JsonResponse({
            'status': 'success',
            'is_inside': True,
            'message': 'You are inside the campus. You can now take attendance.'
        })
    else:
        return JsonResponse({
            'status': 'error',
            'is_inside': False,
            'message': 'You are outside the campus. Attendance not allowed.'
        })
    
@login_required
def face_recognition_page(request):
    # Allow access only if the 'verified' query parameter is present and equals '1'
    #print(f"Face recognition page accessed with query params: {request.GET}")
    if request.GET.get('verified') != '1':
        return redirect('student_dashboard')
    # Optional: also clear session or keep it
    return render(request, 'attendance/face_recognition.html')


from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Count, Q
from accounts.models import StudentProfile
from attendance.models import *

@staff_member_required(login_url='login')
def admin_dashboard(request):
    """Render the admin dashboard HTML"""
    return render(request, 'admin_dashboard.html')

@require_http_methods(['GET'])
def api_courses(request):
    """Return list of all courses with student count"""
    courses = StudentProfile.objects.values('course').annotate(
        student_count=Count('id')
    ).order_by('course')
    
    # Optionally add full name and icon for each course
    course_details = {
        'BBA': {'full_name': 'Bachelor of Business Administration', 'icon': 'fas fa-chart-line'},
        'BCA': {'full_name': 'Bachelor of Computer Applications', 'icon': 'fas fa-laptop-code'},
        'BCOM': {'full_name': 'Bachelor of Commerce', 'icon': 'fas fa-chart-pie'},
        'BA': {'full_name': 'Bachelor of Arts', 'icon': 'fas fa-landmark'},
        'BSC': {'full_name': 'Bachelor of Science', 'icon': 'fas fa-flask'},
    }
    
    data = []
    for course in courses:
        course_name = course['course']
        data.append({
            'short_name': course_name,
            'full_name': course_details.get(course_name, {}).get('full_name', course_name),
            'icon': course_details.get(course_name, {}).get('icon', 'fas fa-graduation-cap'),
            'student_count': course['student_count'],
        })
    return JsonResponse({'departments': data})

import logging
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from accounts.models import StudentProfile
from attendance.models import AttendanceRecord

logger = logging.getLogger(__name__)

@require_http_methods(['GET'])
def api_course_students(request, course_name):
    # Get the current time in Django's configured timezone
    now = timezone.localtime()  # returns local time (e.g., Asia/Kolkata)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timezone.timedelta(days=1)

    print(f"[DEBUG] Today's range: {today_start} to {today_end}")

    students = StudentProfile.objects.filter(course=course_name).select_related('user')
    if not students.exists():
        return JsonResponse({'error': 'Course not found'}, status=404)

    # Query using the `created_at` datetime field – timezone‑aware
    records = AttendanceRecord.objects.filter(
        student__in=students,
        created_at__gte=today_start,
        created_at__lt=today_end
    ).select_related('student')

    print(f"[DEBUG] Found {records.count()} attendance records for today")

    attendance_map = {}
    for rec in records:
        raw_status = rec.status
        normalized = raw_status.strip().lower() if raw_status else ''
        if normalized == 'present':
            status = 'Present'
        elif normalized == 'absent':
            status = 'Absent'
        else:
            status = raw_status
        attendance_map[rec.student.id] = status
        print(f"[DEBUG] Student {rec.student.roll_no} -> raw '{raw_status}' -> normalized '{status}'")

    students_data = []
    for student in students:
        status = attendance_map.get(student.id, 'Absent')
        students_data.append({
            'id': student.roll_no,
            'name': student.user.get_full_name() or student.user.username,
            'status': status,
        })
        print(f"[DEBUG] {student.roll_no}: final status = {status}")

    present_count = sum(1 for s in students_data if s['status'] == 'Present')
    absent_count = sum(1 for s in students_data if s['status'] == 'Absent')

    response_data = {
        'department': {
            'short_name': course_name,
            'full_name': course_name,
            'icon': 'fas fa-users',
        },
        'students': students_data,
        'present_count': present_count,
        'absent_count': absent_count,
        'total_students': len(students_data),
        '_debug': {
            'date_range_used': f"{today_start.date()}",
            'records_found': records.count(),
        }
    }
    return JsonResponse(response_data)