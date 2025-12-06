"""
Utility functions for posts app.
"""

import re
from users.models import User


def extract_mentions(text):
    """
    Extract @username mentions from text.
    Returns list of User objects.
    """
    # Find all @username patterns
    pattern = r'@(\w+)'
    usernames = re.findall(pattern, text)
    
    if not usernames:
        return []
    
    # Get users that exist
    mentioned_users = User.objects.filter(username__in=usernames)
    
    return list(mentioned_users)


def create_comment_notification(comment, mentioned_users=None):
    """
    Create notifications for comment.
    - Notify post owner
    - Notify mentioned users
    - Notify parent comment owner (for replies)
    """
    from notifications.models import Notification
    
    notifications_to_create = []
    notified_users = set()
    
    # Notify post owner (if not commenter)
    if comment.post.user != comment.user and comment.post.user not in notified_users:
        notifications_to_create.append(
            Notification(
                recipient=comment.post.user,
                sender=comment.user,
                notification_type='comment',
                text=f'{comment.user.username} commented on your post',
                link=f'/posts/{comment.post.id}/'
            )
        )
        notified_users.add(comment.post.user)
    
    # Notify parent comment owner (for replies)
    if comment.parent_comment and comment.parent_comment.user != comment.user:
        if comment.parent_comment.user not in notified_users:
            notifications_to_create.append(
                Notification(
                    recipient=comment.parent_comment.user,
                    sender=comment.user,
                    notification_type='comment',
                    text=f'{comment.user.username} replied to your comment',
                    link=f'/posts/{comment.post.id}/'
                )
            )
            notified_users.add(comment.parent_comment.user)
    
    # Notify mentioned users
    if mentioned_users:
        for user in mentioned_users:
            if user != comment.user and user not in notified_users:
                notifications_to_create.append(
                    Notification(
                        recipient=user,
                        sender=comment.user,
                        notification_type='mention',
                        text=f'{comment.user.username} mentioned you in a comment',
                        link=f'/posts/{comment.post.id}/'
                    )
                )
                notified_users.add(user)
    
    # Bulk create notifications
    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create)
    
    return len(notifications_to_create)
