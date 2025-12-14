"""
Custom middleware for performance and security
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import time
import hashlib


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent abuse
    Limits requests per IP address
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = 100  # requests per minute
        self.window = 60  # 60 seconds
        
    def process_request(self, request):
        # Skip rate limiting for health checks and static files
        if request.path.startswith('/health/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
            
        # Get client IP
        ip = self.get_client_ip(request)
        
        # Create cache key
        cache_key = f'rate_limit:{ip}'
        
        # Get current request count
        request_count = cache.get(cache_key, 0)
        
        if request_count >= self.rate_limit:
            return JsonResponse({
                'error': 'Rate limit exceeded. Please try again later.',
                'limit': self.rate_limit,
                'window': self.window
            }, status=429)
        
        # Increment counter
        cache.set(cache_key, request_count + 1, self.window)
        
        return None
    
    def get_client_ip(self, request):
        """Get the client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RequestTimingMiddleware(MiddlewareMixin):
    """
    Middleware to track request timing for monitoring
    """
    
    def process_request(self, request):
        request.start_time = time.time()
        
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            response['X-Request-Duration'] = str(duration)
            
            # Log slow requests (> 1 second)
            if duration > 1.0:
                import logging
                logger = logging.getLogger('django.request')
                logger.warning(
                    f'Slow request: {request.method} {request.path} took {duration:.2f}s'
                )
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    
    def process_response(self, request, response):
        # Only add headers if not already set
        if 'X-Content-Type-Options' not in response:
            response['X-Content-Type-Options'] = 'nosniff'
        
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'DENY'
        
        if 'X-XSS-Protection' not in response:
            response['X-XSS-Protection'] = '1; mode=block'
        
        if 'Referrer-Policy' not in response:
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response