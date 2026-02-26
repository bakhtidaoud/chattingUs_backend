import os
import boto3
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Backup database and media to S3'

    def handle(self, *args, **options):
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 1. Backup DB (SQLite for now)
        db_path = settings.DATABASES['default']['NAME']
        db_filename = f"backups/db_{timestamp}.sqlite3"
        
        self.stdout.write(f"Backing up database to {db_filename}...")
        try:
            s3.upload_file(str(db_path), bucket, db_filename)
            self.stdout.write(self.style.SUCCESS('Database backup successful!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"DB Backup failed: {e}"))

        # 2. Backup Media (Zip and upload)
        media_root = settings.MEDIA_ROOT
        media_zip = f"media_{timestamp}.zip"
        media_s3_path = f"backups/{media_zip}"

        self.stdout.write(f"Zipping media folder...")
        # Simple zip command (platform dependent, using shutil for better portability)
        import shutil
        shutil.make_archive(f"tmp_media_{timestamp}", 'zip', media_root)
        
        self.stdout.write(f"Uploading media backup to {media_s3_path}...")
        try:
            s3.upload_file(f"tmp_media_{timestamp}.zip", bucket, media_s3_path)
            os.remove(f"tmp_media_{timestamp}.zip")
            self.stdout.write(self.style.SUCCESS('Media backup successful!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Media Backup failed: {e}"))
