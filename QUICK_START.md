# Quick Database Creation Guide

## Create Database in pgAdmin

1. **Open pgAdmin** and connect to your PostgreSQL server

2. **Right-click on "Databases"** in the left sidebar (under your PostgreSQL server)

3. **Select "Create" → "Database..."**

4. **In the dialog that opens:**
   - **Database name:** `chattingus_db`
   - **Owner:** `postgres` (or your PostgreSQL username)
   - Click **"Save"**

5. **Verify:** You should now see `chattingus_db` in the Databases list

## After Creating the Database

Run these commands in your project directory:

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run migrations to create all tables
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser

# Create media and backup directories
mkdir media
mkdir backups
```

## Test the Setup

```powershell
# Run Django checks
python manage.py check

# Start the development server
python manage.py runserver
```

Then visit:
- **Admin Panel:** http://localhost:8000/admin/
- **API Root:** http://localhost:8000/api/

## Troubleshooting

If you get connection errors:
1. Make sure PostgreSQL service is running
2. Verify your password in the `.env` file (currently set to `Luffy2020`)
3. Check that PostgreSQL is listening on port 5432
