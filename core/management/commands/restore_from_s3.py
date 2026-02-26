import os
import boto3
import zipfile
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Restore database and media from S3'

    def add_arguments(self, parser):
        parser.add_argument('db_backup', type=str, help='S3 key of the DB backup')
        parser.add_argument('media_backup', type=str, help='S3 key of the media backup')

    def handle(self, *args, **options):
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        
        # 1. Restore DB
        db_path = settings.DATABASES['default']['NAME']
        db_key = options['db_backup']
        
        self.stdout.write(f"Downloading DB from {db_key}...")
        try:
            # Backup current DB first (safety)
            if os.path.exists(db_path):
                shutil.copy2(db_path, f"{db_path}.before_restore")
            
            s3.download_file(bucket, db_key, str(db_path))
            self.stdout.write(self.style.SUCCESS(f'Database restored from {db_key}!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"DB restore failed: {e}"))

        # 2. Restore Media
        media_root = settings.MEDIA_ROOT
        media_key = options['media_backup']
        
        self.stdout.write(f"Downloading and extracting media from {media_key}...")
        try:
             # Download as zip
            zip_filename = "restore_media.zip"
            s3.download_file(bucket, media_key, zip_filename)
            
            # Extract to media root
            if not os.path.exists(media_root):
                os.makedirs(media_root)
            
            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall(media_root)
            
            os.remove(zip_filename)
            self.stdout.write(self.style.SUCCESS(f'Media restored from {media_key}!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Media restore failed: {e}"))
