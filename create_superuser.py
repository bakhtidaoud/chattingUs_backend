"""
Script to create a Django superuser programmatically
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chattingus_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Superuser credentials
email = 'admin@chattingus.com'
username = 'admin'
password = 'Admin@123456'

# Check if superuser already exists (check by username first)
if User.objects.filter(username=username).exists():
    print(f'Superuser with username "{username}" already exists!')
    user = User.objects.get(username=username)
    # Update email and password
    user.email = email
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print('Superuser updated successfully!')
elif User.objects.filter(email=email).exists():
    print(f'User with email {email} already exists!')
    user = User.objects.get(email=email)
    # Update password and make superuser
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print('User updated to superuser!')
else:
    # Create superuser
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f'Superuser created successfully!')

print('\n' + '='*50)
print('SUPERUSER CREDENTIALS')
print('='*50)
print(f'Email: {email}')
print(f'Username: {username}')
print(f'Password: {password}')
print('='*50)

# Save credentials to file
with open('user_credentials.txt', 'w') as f:
    f.write('ChattingUs Admin Dashboard - Superuser Credentials\n')
    f.write('='*50 + '\n\n')
    f.write(f'Email: {email}\n')
    f.write(f'Username: {username}\n')
    f.write(f'Password: {password}\n\n')
    f.write('='*50 + '\n')
    f.write('Use these credentials to login to:\n')
    f.write('- Admin Dashboard: http://localhost:8000/admin-dashboard/\n')
    f.write('- Django Admin: http://localhost:8000/admin/\n')

print('\nCredentials saved to: user_credentials.txt')
