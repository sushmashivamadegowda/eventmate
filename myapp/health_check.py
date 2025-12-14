"""
Health check and monitoring endpoints
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.db import connection
from django.core.cache import cache
import time


@never_cache
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if the service is healthy
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time()
    })


@never_cache
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Readiness check - verifies all dependencies are available
    """
    checks = {
        'database': False,
        'cache': False,
        'overall': False
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            checks['database'] = True
    except Exception as e:
        checks['database_error'] = str(e)
    
    # Check cache (Redis)
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['cache'] = True
        cache.delete('health_check')
    except Exception as e:
        checks['cache_error'] = str(e)
    
    # Overall status
    checks['overall'] = checks['database'] and checks['cache']
    
    status_code = 200 if checks['overall'] else 503
    
    return JsonResponse({
        'status': 'ready' if checks['overall'] else 'not ready',
        'checks': checks,
        'timestamp': time.time()
    }, status=status_code)


@never_cache
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Liveness check - verifies the application process is alive
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': time.time()
    })


@never_cache  
@require_http_methods(["GET"])
def metrics(request):
    """
    Basic metrics endpoint
    """
    from django.db import connections
    from myapp.models import Event, Booking, User
    
    try:
        # Database connection pool status
        db = connections['default']
        
        # Get basic stats
        stats = {
            'active_events': Event.objects.filter(is_active=True).count(),
            'total_users': User.objects.count(),
            'total_bookings': Booking.objects.count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'confirmed_bookings': Booking.objects.filter(status='confirmed').count(),
        }
        
        return JsonResponse({
            'status': 'ok',
            'metrics': stats,
            'timestamp': time.time()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        }, status=500)