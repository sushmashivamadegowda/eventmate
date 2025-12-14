from .models import City

def cities_context(request):
    """Add cities to all template contexts"""
    cities = City.objects.filter(
        events__is_active=True
    ).distinct().order_by('name')
    return {
        'cities': cities
    }