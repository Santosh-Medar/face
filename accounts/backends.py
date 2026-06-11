from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import StudentProfile

class DualAuthenticationBackend(ModelBackend):
    """
    Authenticate using:
    - roll_no (case‑insensitive, for students) OR
    - username (case‑sensitive, for admins)
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Try to interpret the input as a roll number (case‑insensitive)
        try:
            student_profile = StudentProfile.objects.get(roll_no__iexact=username)
            user = student_profile.user
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except StudentProfile.DoesNotExist:
            # Not a roll number – fall back to default username authentication
            return super().authenticate(request, username=username, password=password, **kwargs)
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None