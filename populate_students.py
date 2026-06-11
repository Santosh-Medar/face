# populate_students.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geoface_attendance.settings')  # change to your project name
django.setup()

from django.contrib.auth.models import User
from accounts.models import StudentProfile  # adjust import path

# List of names extracted from the image filenames
names = [
    "Adani",
    "Ambani",
    "Bhaskar",
    "Elon Musk",
    "Mark Zuckerberg",
    "Sreekanth",
    "Vidya",
    "Virat Kohli"
]

def create_students():
    base_roll = "u16sd23s"   # prefix
    start_num = 1
    default_password = "student123"
    default_course = "BCA"      # change as needed
    default_semester = "6"      # change as needed

    created_count = 0
    for idx, name in enumerate(names, start=start_num):
        roll_number = f"{base_roll}{idx:04d}"   # e.g., u16sd23s0001, u16sd23s0002
        username = roll_number                   # use roll number as username (or name.lower().replace(' ', '_'))
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User {username} already exists, skipping...")
            continue
        
        # Create User
        user = User.objects.create_user(
            username=username,
            password=default_password,
            first_name=name.split()[0],
            last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else ""
        )
        
        # Create StudentProfile
        student_profile = StudentProfile.objects.create(
            user=user,
            roll_no=roll_number,
            course=default_course,
            semester=default_semester,
            phone="",          # optional
        )
        created_count += 1
        print(f"Created: {name} -> {roll_number} (username: {username})")

    print(f"\n✅ Successfully created {created_count} students.")
    print(f"Default password for all: {default_password}")

if __name__ == "__main__":
    create_students()