"""
Users API for Admin Dashboard
Provides real user data from the database
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q

User = get_user_model()


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def users_list(request):
    """
    Get list of users from database
    """
    # Get query parameters
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    search = request.GET.get('search', '')
    
    # Get all users
    users = User.objects.all().order_by('-date_joined')
    
    # Apply search filter if provided
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Paginate
    paginator = Paginator(users, page_size)
    page_obj = paginator.get_page(page)
    
    # Serialize users
    users_data = []
    for user in page_obj:
        # Check if user has is_verified field
        is_verified = getattr(user, 'is_verified', False)
        
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_verified': is_verified,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        })
    
    return Response({
        'count': paginator.count,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous(),
        'results': users_data,
        'total_pages': paginator.num_pages,
        'current_page': page
    })


@api_view(['GET', 'PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([AllowAny])
def user_detail_or_update(request, pk):
    """
    Get or update user details
    """
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    
    # GET - Return user details
    if request.method == 'GET':
        is_verified = getattr(user, 'is_verified', False)
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_verified': is_verified,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        })
    
    # PUT/PATCH - Update user
    else:
        # Update user fields
        if 'username' in request.data:
            user.username = request.data['username']
        if 'email' in request.data:
            user.email = request.data['email']
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        if 'is_active' in request.data:
            user.is_active = request.data['is_active']
        if 'is_staff' in request.data:
            user.is_staff = request.data['is_staff']
        if 'is_verified' in request.data and hasattr(user, 'is_verified'):
            user.is_verified = request.data['is_verified']
        
        user.save()
        
        is_verified = getattr(user, 'is_verified', False)
        
        return Response({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name or '',
                'last_name': user.last_name or '',
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_verified': is_verified,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
        })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def user_verify(request, pk):
    """
    Verify or unverify a user
    """
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    
    # Check if user model has is_verified field
    if hasattr(user, 'is_verified'):
        # Toggle verification status
        user.is_verified = not user.is_verified
        user.save()
        
        return Response({
            'success': True,
            'is_verified': user.is_verified,
            'message': f'User {"verified" if user.is_verified else "unverified"} successfully'
        })
    else:
        return Response({
            'error': 'User model does not have is_verified field'
        }, status=400)


@api_view(['PUT', 'PATCH'])
@authentication_classes([])
@permission_classes([AllowAny])
def user_update(request, pk):
    """
    Update user information
    """
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    
    # Update user fields
    if 'username' in request.data:
        user.username = request.data['username']
    if 'email' in request.data:
        user.email = request.data['email']
    if 'first_name' in request.data:
        user.first_name = request.data['first_name']
    if 'last_name' in request.data:
        user.last_name = request.data['last_name']
    if 'is_active' in request.data:
        user.is_active = request.data['is_active']
    if 'is_staff' in request.data:
        user.is_staff = request.data['is_staff']
    if 'is_verified' in request.data and hasattr(user, 'is_verified'):
        user.is_verified = request.data['is_verified']
    
    user.save()
    
    is_verified = getattr(user, 'is_verified', False)
    
    return Response({
        'success': True,
        'message': 'User updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_verified': is_verified,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
    })
