from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse


def role_required(*allowed_roles):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # AJAX / API requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept', ''):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Access restricted to authorized roles.'
                }, status=403)

            # Standard browser navigation - graceful redirect instead of 403 crash
            messages.warning(request, 'Access Restricted: You do not have permission to access that section.')
            return redirect('dashboard')

        return wrapper

    return decorator
