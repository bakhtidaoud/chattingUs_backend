# Database Setup Instructions

## Step 1: Create PostgreSQL Database

You have two options to create the database:

### Option A: Using pgAdmin (GUI)
1. Open pgAdmin
2. Right-click on "Databases"
3. Select "Create" → "Database"
4. Enter database name: `chattingus_db`
5. Click "Save"

### Option B: Using psql Command Line
1. Open Command Prompt or PowerShell
2. Navigate to PostgreSQL bin directory (usually `C:\Program Files\PostgreSQL\<version>\bin`)
3. Run: `psql -U postgres`
4. Enter your PostgreSQL password when prompted
5. Run: `CREATE DATABASE chattingus_db;`
6. Run: `\q` to exit

## Step 2: Run Django Migrations

After creating the database, run the following commands in your project directory:

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run migrations
python manage.py migrate

# Create a superuser (admin account)
python manage.py createsuperuser

# Create media directory
mkdir media
mkdir backups
```

## Step 3: Apply Performance Indexes (Optional but Recommended)

After running migrations, you can apply the performance indexes:

### Using pgAdmin:
1. Open pgAdmin and connect to `chattingus_db`
2. Open the Query Tool
3. Copy and paste the contents of `database_setup.sql` (skip the CREATE DATABASE line)
4. Execute the query

### Using psql:
```powershell
psql -U postgres -d chattingus_db -f database_setup.sql
```

## Step 4: Test the Setup

```powershell
# Run Django checks
python manage.py check

# Start the development server
python manage.py runserver
```

Visit `http://localhost:8000/admin/` to access the admin panel.

## Database Backup

To create a backup of your database:

```powershell
python backup_database.py
```

To restore from a backup:

```powershell
python backup_database.py restore backups\chattingus_db_backup_YYYYMMDD_HHMMSS.sql
```

Backups are automatically rotated, keeping the last 7 backups by default (configurable in `.env` with `DB_BACKUP_COUNT`).
