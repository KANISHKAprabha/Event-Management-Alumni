# middleware.py
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            logger.error(f"Unhandled error: {e}", exc_info=True)
            return render(request, "errors/error.html", status=500)
