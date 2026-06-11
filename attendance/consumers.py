import json
import base64
import numpy as np
import cv2
import face_recognition
from io import BytesIO
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from accounts.models import StudentProfile
from .models import AttendanceRecord, CampusBoundary
from shapely.geometry import Point, Polygon

class FaceDetectionConsumer(AsyncWebsocketConsumer):
    # Instance variables (per connection)
    student_encoding = None
    student_profile = None
    student_name = None

    async def connect(self):
        await self.accept()
        print("🟢 WebSocket Connected")

    async def disconnect(self, close_code):
        print("🔴 WebSocket Disconnected")

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Initial setup from frontend – load the encoding for the logged-in student
        if data.get("action") == "init":
            roll_no = data.get("roll_no")   # received from frontend
            await self.load_encoding_for_student(roll_no)
            return

        # Stop button
        if data.get("action") == "stop":
            await self.close()
            return

        # Frame data with location
        frame_data = data.get("frame")
        lat = data.get("lat")
        lon = data.get("lon")

        if frame_data and lat is not None and lon is not None:
            is_inside = await self.is_within_campus(lat, lon)
            if is_inside:
                faces = await self.detect_faces(frame_data, lat, lon)
                await self.send(text_data=json.dumps({'faces': faces}))
            else:
                await self.send(text_data=json.dumps({'error': 'Outside campus'}))

    async def detect_faces(self, frame_data, lat, lon):
        """Detect faces, compare only with the logged-in student's encoding."""
        if self.student_encoding is None:
            return []   # no encoding loaded

        try:
            # Decode base64 image
            if ',' in frame_data:
                frame_data = frame_data.split(',')[1]
            img_bytes = base64.b64decode(frame_data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect face locations and encodings
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            recognized_faces = []
            for encode_face, face_loc in zip(face_encodings, face_locations):
                # Compare with the single known encoding
                matches = face_recognition.compare_faces([self.student_encoding], encode_face, tolerance=0.6)
                if matches[0]:
                    # Mark attendance
                    await self.mark_attendance(lat, lon)

                    top, right, bottom, left = face_loc
                    recognized_faces.append({
                        "x": int(left),
                        "y": int(top),
                        "width": int(right - left),
                        "height": int(bottom - top),
                        "name": self.student_name
                    })
            return recognized_faces
        except Exception as e:
            print(f"⚠️ Error in detect_faces: {e}")
            return []

    @sync_to_async
    def is_within_campus(self, lat, lon):
        boundary = CampusBoundary.objects.filter(is_active=True).first()
        if not boundary or not boundary.boundary:
            return False
        poly_coords = boundary.boundary
        if poly_coords[0] != poly_coords[-1]:
            poly_coords = poly_coords + [poly_coords[0]]
        campus_polygon = Polygon(poly_coords)
        student_point = Point(lon, lat)
        buffered_polygon = campus_polygon.buffer(0.00015)
        return buffered_polygon.contains(student_point)

    @sync_to_async
    def mark_attendance(self, lat, lon):
        """Mark attendance for the logged-in student."""
        if self.student_profile is None:
            return
        today = timezone.now().date()
        attendance, created = AttendanceRecord.objects.get_or_create(
            student=self.student_profile,
            date=today,
            defaults={
                'latitude': lat,
                'longitude': lon,
                'location_verified': True,
                'face_verified': True,
                'status': 'Present'
            }
        )
        if not created and not attendance.face_verified:
            attendance.face_verified = True
            attendance.status = 'Present'
            attendance.latitude = lat
            attendance.longitude = lon
            attendance.save()
            print(f"✅ Attendance updated: {self.student_name}")
        elif created:
            print(f"✅ Attendance marked: {self.student_name}")

    @sync_to_async
    def load_encoding_for_student(self, roll_no):
        """Load face encoding and student profile for the given roll number."""
        try:
            student = StudentProfile.objects.get(roll_no=roll_no)
            if student.face_encoding:
                encoding_list = json.loads(student.face_encoding)
                self.student_encoding = np.array(encoding_list)
                self.student_profile = student
                self.student_name = student.user.get_full_name() or student.user.username
                print(f"✅ Loaded encoding for {self.student_name} (roll: {roll_no})")
            else:
                print(f"⚠️ No face encoding found for student {roll_no}")
        except StudentProfile.DoesNotExist:
            print(f"❌ Student with roll number {roll_no} not found")