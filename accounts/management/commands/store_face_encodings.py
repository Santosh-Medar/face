import json
import logging
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
from accounts.models import StudentProfile  

try:
    import face_recognition
except ImportError:
    raise ImportError("face_recognition library is not installed. Run: pip install face_recognition")

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate and store face encodings for StudentProfile instances that have a face_image.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recompute encoding even if face_encoding already exists.',
        )
        parser.add_argument(
            '--roll-no',
            type=str,
            help='Process only a specific roll number.',
        )

    def handle(self, *args, **options):
        force = options['force']
        roll_no = options.get('roll_no')

        queryset = StudentProfile.objects.exclude(face_image='')
        if roll_no:
            queryset = queryset.filter(roll_no=roll_no)

        if not queryset.exists():
            self.stdout.write(self.style.WARNING("No StudentProfile with face_image found."))
            return

        updated_count = 0
        skipped_count = 0
        error_count = 0

        for profile in queryset:
            if profile.face_encoding and not force:
                self.stdout.write(f"Skipping {profile.roll_no} (encoding already exists)")
                skipped_count += 1
                continue

            # Get absolute path of the image
            image_path = profile.face_image.path
            if not default_storage.exists(profile.face_image.name):
                self.stdout.write(self.style.ERROR(f"Image file missing for {profile.roll_no}: {image_path}"))
                error_count += 1
                continue

            try:
                # Load image and compute face encodings
                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)

                if not encodings:
                    self.stdout.write(self.style.WARNING(f"No face detected in image for {profile.roll_no}"))
                    error_count += 1
                    continue

                # Use the first detected face encoding
                encoding_list = encodings[0].tolist()  # numpy array -> list of floats
                encoding_json = json.dumps(encoding_list)

                # Save to database
                profile.face_encoding = encoding_json
                profile.save(update_fields=['face_encoding'])
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Stored encoding for {profile.roll_no}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {profile.roll_no}: {str(e)}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}"
        ))