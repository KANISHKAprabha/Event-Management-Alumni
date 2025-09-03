# my_event_app/decorators.py

from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps
from django.contrib import messages  # <-- IMPORT THE MESSAGES FRAMEWORK


def event_login_required(view_func):
    """
    Custom decorator for event views.
    Checks if a user is logged in. If not, redirects to the 
    event registration info page instead of the default login page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # The URL name of your "Please register for the event" page
            register_url = reverse('event_overview') 
            messages.info(request, "Please register or log in to view the event details.")

            return redirect(register_url)
        return view_func(request, *args, **kwargs)
    return _wrapped_view