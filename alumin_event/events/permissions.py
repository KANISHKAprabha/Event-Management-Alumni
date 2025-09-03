def is_admin(user):
    """Check if user is Admin (superuser or in Admin group)"""
    return user.is_superuser or user.groups.filter(name="Admin").exists()


def is_user(user):
    """Check if user is a regular User (anyone not admin, or in 'User' group)"""
    # Users inherit permissions from admin
    return user.groups.filter(name="User").exists() or is_admin(user)
