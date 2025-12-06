"""
Database backup script for Chattingus Backend.
Creates a backup of the PostgreSQL database.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from decouple import config

# Configuration
DB_NAME = config('DB_NAME', default='chattingus_db')
DB_USER = config('DB_USER', default='postgres')
DB_PASSWORD = config('DB_PASSWORD', default='')
DB_HOST = config('DB_HOST', default='localhost')
DB_PORT = config('DB_PORT', default='5432')

# Backup directory
BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / 'backups'
BACKUP_COUNT = config('DB_BACKUP_COUNT', default=7, cast=int)

# Create backup directory if it doesn't exist
BACKUP_DIR.mkdir(exist_ok=True)

def create_backup():
    """Create a database backup."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'{DB_NAME}_backup_{timestamp}.sql'
    
    # Set password environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASSWORD
    
    # Create backup using pg_dump
    command = [
        'pg_dump',
        '-h', DB_HOST,
        '-p', DB_PORT,
        '-U', DB_USER,
        '-F', 'p',  # Plain text format
        '-f', str(backup_file),
        DB_NAME
    ]
    
    try:
        subprocess.run(command, env=env, check=True)
        print(f'✓ Backup created successfully: {backup_file}')
        cleanup_old_backups()
        return True
    except subprocess.CalledProcessError as e:
        print(f'✗ Backup failed: {e}')
        return False
    except FileNotFoundError:
        print('✗ pg_dump command not found. Please ensure PostgreSQL is installed and in PATH.')
        return False

def cleanup_old_backups():
    """Remove old backups, keeping only the most recent ones."""
    backups = sorted(BACKUP_DIR.glob(f'{DB_NAME}_backup_*.sql'))
    
    if len(backups) > BACKUP_COUNT:
        for backup in backups[:-BACKUP_COUNT]:
            backup.unlink()
            print(f'✓ Removed old backup: {backup.name}')

def restore_backup(backup_file):
    """Restore database from a backup file."""
    if not Path(backup_file).exists():
        print(f'✗ Backup file not found: {backup_file}')
        return False
    
    # Set password environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASSWORD
    
    # Restore using psql
    command = [
        'psql',
        '-h', DB_HOST,
        '-p', DB_PORT,
        '-U', DB_USER,
        '-d', DB_NAME,
        '-f', backup_file
    ]
    
    try:
        subprocess.run(command, env=env, check=True)
        print(f'✓ Database restored successfully from: {backup_file}')
        return True
    except subprocess.CalledProcessError as e:
        print(f'✗ Restore failed: {e}')
        return False
    except FileNotFoundError:
        print('✗ psql command not found. Please ensure PostgreSQL is installed and in PATH.')
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) < 3:
            print('Usage: python backup_database.py restore <backup_file>')
            sys.exit(1)
        restore_backup(sys.argv[2])
    else:
        create_backup()
