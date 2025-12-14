from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime, timedelta
from .models import Event, City, Booking, Review, EventImage, Favorite, User
from .forms import EventForm, BookingForm, ReviewForm, EventSearchForm


class EventListView(ListView):
    """Main event listing with search and filters"""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        # Only return results if there are active filters
        query_params = self.request.GET
        
        if any(query_params.get(param) for param in ['q', 'location', 'category', 'city', 'date', 'type', 'min_price', 'max_price']):
            queryset = Event.objects.filter(
                is_active=True,
                start_date__gte=datetime.now().date()
            ).select_related('city', 'host').prefetch_related('images', 'reviews')
            
            # Search query
            search_query = query_params.get('q', '').strip()
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(location__icontains=search_query) |
                    Q(city__name__icontains=search_query) |
                    Q(category__icontains=search_query)
                )
            
            # Location filter
            location = query_params.get('location', '').strip()
            if location:
                queryset = queryset.filter(
                    Q(city__name__icontains=location) |
                    Q(location__icontains=location) |
                    Q(city__state__icontains=location)
                )
            
            # Category filter
            category = query_params.get('category', '').strip()
            if category and category != 'all':
                queryset = queryset.filter(category=category)
            
            # City filter (by slug)
            city = query_params.get('city', '').strip()
            if city:
                queryset = queryset.filter(city__slug=city)
            
            # Date filter
            date = query_params.get('date', '').strip()
            if date:
                try:
                    event_date = datetime.strptime(date, '%Y-%m-%d').date()
                    queryset = queryset.filter(
                        start_date__lte=event_date,
                        end_date__gte=event_date
                    )
                except ValueError:
                    pass
            
            # Event type filter
            event_type = query_params.get('type', '').strip()
            if event_type:
                queryset = queryset.filter(category__icontains=event_type)
            
            # Price range filter
            min_price = query_params.get('min_price', '').strip()
            max_price = query_params.get('max_price', '').strip()
            if min_price:
                try:
                    queryset = queryset.filter(price__gte=float(min_price))
                except (ValueError, TypeError):
                    pass
            if max_price:
                try:
                    queryset = queryset.filter(price__lte=float(max_price))
                except (ValueError, TypeError):
                    pass
            
            # Sort options
            sort = query_params.get('sort', '-created_at')
            if sort == 'price':
                queryset = queryset.order_by('price')
            elif sort == '-price':
                queryset = queryset.order_by('-price')
            elif sort == 'start_date':
                queryset = queryset.order_by('start_date')
            elif sort == 'popular':
                queryset = queryset.annotate(
                    booking_count=Count('bookings')
                ).order_by('-booking_count')
            else:
                queryset = queryset.order_by(sort)
            
            return queryset.distinct()
        
        # Return empty queryset for homepage (we'll show curated sections instead)
        return Event.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # All cities for dropdown
        context['cities'] = City.objects.filter(
            events__is_active=True
        ).distinct().order_by('name')
        
        # Featured cities with event counts
        context['featured_cities'] = City.objects.filter(
            is_featured=True
        ).annotate(
            event_count=Count('events', filter=Q(
                events__is_active=True, 
                events__start_date__gte=datetime.now().date()
            ))
        ).order_by('-event_count')[:3]
        
        # Categories
        context['categories'] = Event.CATEGORY_CHOICES
        
        # Search form
        context['search_form'] = EventSearchForm(self.request.GET)
        
        # Active filters
        context['active_filters'] = {
            'q': self.request.GET.get('q', ''),
            'location': self.request.GET.get('location', ''),
            'category': self.request.GET.get('category', ''),
            'city': self.request.GET.get('city', ''),
            'date': self.request.GET.get('date', ''),
            'type': self.request.GET.get('type', ''),
        }
        
        # If no filters, show curated sections
        if not any(context['active_filters'].values()):
            # Popular Events (by booking count)
            context['popular_events'] = Event.objects.filter(
                is_active=True,
                start_date__gte=datetime.now().date()
            ).annotate(
                booking_count=Count('bookings')
            ).select_related('city', 'host').prefetch_related('images').order_by(
                '-booking_count', '-created_at'
            )[:10]
            
            # Events grouped by popular cities
            popular_cities = City.objects.filter(
                events__is_active=True,
                events__start_date__gte=datetime.now().date()
            ).annotate(
                event_count=Count('events')
            ).order_by('-event_count')[:5]
            
            events_by_city = []
            for city in popular_cities:
                city_events = Event.objects.filter(
                    city=city,
                    is_active=True,
                    start_date__gte=datetime.now().date()
                ).select_related('city', 'host').prefetch_related('images').order_by(
                    '-created_at'
                )[:8]
                
                if city_events:
                    events_by_city.append({
                        'city': city,
                        'events': city_events
                    })
            
            context['events_by_city'] = events_by_city
        
        # Total results count
        context['total_results'] = self.get_queryset().count()
        
        return context


class EventDetailView(DetailView):
    """Event detail page"""
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    slug_field = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        
        # Reviews with average rating
        context['reviews'] = event.reviews.select_related('user').order_by('-created_at')[:10]
        context['average_rating'] = event.average_rating()
        context['review_count'] = event.review_count()
        
        # Booking form
        context['booking_form'] = BookingForm()
        
        # Check if user has favorited
        if self.request.user.is_authenticated:
            context['is_favorited'] = Favorite.objects.filter(
                user=self.request.user,
                event=event
            ).exists()
        
        # Similar events
        context['similar_events'] = Event.objects.filter(
            category=event.category,
            is_active=True
        ).exclude(id=event.id)[:3]
        
        # Add today's date for template comparison
        context['today'] = datetime.now().date()
        
        return context


@login_required
def create_event(request):
    """Create new event (hosts only)"""
    if not request.user.is_host:
        messages.error(request, 'Only registered hosts can create events.')
        return redirect('event_list')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.host = request.user
            event.save()
            
            # Handle multiple images
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                EventImage.objects.create(
                    event=event,
                    image=image,
                    is_primary=(i == 0),
                    order=i
                )
            
            messages.success(request, 'Event created successfully!')
            return redirect('event_detail', slug=event.slug)
    else:
        form = EventForm()
    
    return render(request, 'events/event_form.html', {'form': form})


@login_required
def update_event(request, slug):
    """Update existing event"""
    event = get_object_or_404(Event, slug=slug, host=request.user)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            
            # Handle new images if uploaded
            images = request.FILES.getlist('images')
            if images:
                # Get the current max order
                max_order = event.images.count()
                for i, image in enumerate(images):
                    EventImage.objects.create(
                        event=event,
                        image=image,
                        is_primary=False,
                        order=max_order + i
                    )
            
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', slug=event.slug)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/event_form.html', {
        'form': form,
        'event': event
    })


@login_required
def create_booking(request, slug):
    """Create booking for an event"""
    event = get_object_or_404(Event, slug=slug, is_active=True)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, event=event)
        if form.is_valid():
            tickets = form.cleaned_data['tickets']
            event_date = form.cleaned_data['event_date']
            
            # Check availability
            if event.available_tickets < tickets:
                messages.error(request, 'Not enough tickets available.')
                return redirect('event_detail', slug=slug)
            
            # Check date validity
            if event_date < event.start_date or event_date > event.end_date:
                messages.error(request, 'Selected date is not valid for this event.')
                return redirect('event_detail', slug=slug)
            
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                event=event,
                tickets=tickets,
                event_date=event_date,
                total_price=event.price * tickets,
                status='pending'
            )
            
            # Update available tickets
            event.available_tickets -= tickets
            event.save()
            
            messages.success(request, 'Booking created! Please proceed to payment.')
            return redirect('booking_confirm', booking_id=booking.id)
    
    messages.error(request, 'Invalid booking request.')
    return redirect('event_detail', slug=slug)


@login_required
def booking_confirm(request, booking_id):
    """Booking confirmation page"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    return render(request, 'events/booking_confirm.html', {
        'booking': booking
    })


@login_required
def process_payment(request, booking_id):
    """Process payment for booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.is_paid:
        messages.info(request, 'This booking is already paid.')
        return redirect('booking_confirm', booking_id=booking.id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method', 'card')
        
        # Here you would integrate with actual payment gateway
        # For now, we'll simulate successful payment
        
        try:
            # Simulate payment processing
            import uuid
            booking.payment_id = str(uuid.uuid4())
            booking.is_paid = True
            booking.status = 'confirmed'
            booking.save()
            
            messages.success(request, 'Payment successful! Your booking is confirmed.')
            return redirect('payment_success', booking_id=booking.id)
            
        except Exception as e:
            messages.error(request, f'Payment failed: {str(e)}')
            return redirect('booking_confirm', booking_id=booking.id)
    
    # GET request - show payment page
    return render(request, 'events/payment.html', {
        'booking': booking
    })


@login_required
def payment_success(request, booking_id):
    """Payment success page"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    return render(request, 'events/payment_success.html', {
        'booking': booking
    })


@login_required
def payment_cancel(request, booking_id):
    """Payment cancelled"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    messages.warning(request, 'Payment was cancelled. Your booking is still pending.')
    return redirect('booking_confirm', booking_id=booking.id)


@login_required
def my_bookings(request):
    """User's booking history"""
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('event', 'event__city').prefetch_related('event__images').order_by('-booking_date')
    
    return render(request, 'events/my_bookings.html', {
        'bookings': bookings,
        'today': datetime.now().date()
    })


@login_required
def my_events(request):
    """Host's event management"""
    if not request.user.is_host:
        messages.error(request, 'Access denied.')
        return redirect('event_list')
    
    events = Event.objects.filter(
        host=request.user
    ).annotate(
        booking_count=Count('bookings'),
        avg_rating=Avg('reviews__rating')
    ).prefetch_related('images', 'bookings', 'bookings__user').order_by('-created_at')
    
    return render(request, 'events/my_events.html', {
        'events': events
    })


@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == 'cancelled':
        messages.warning(request, 'Booking is already cancelled.')
        return redirect('my_bookings')
    
    # Check cancellation policy (7 days before event)
    days_until_event = (booking.event_date - datetime.now().date()).days
    
    if days_until_event < 3:
        messages.error(request, 'Cannot cancel within 3 days of the event.')
        return redirect('my_bookings')
    
    # Cancel and refund tickets
    booking.status = 'cancelled'
    booking.save()
    
    booking.event.available_tickets += booking.tickets
    booking.event.save()
    
    refund_percentage = 100 if days_until_event >= 7 else 50
    messages.success(request, f'Booking cancelled. {refund_percentage}% refund will be processed.')
    
    return redirect('my_bookings')


@login_required
def add_review(request, slug):
    """Add review for an event"""
    event = get_object_or_404(Event, slug=slug)
    
    # Check if user has booking for this event
    has_booking = Booking.objects.filter(
        user=request.user,
        event=event,
        status__in=['completed', 'confirmed']
    ).exists()
    
    if not has_booking:
        messages.error(request, 'You can only review events you have booked.')
        return redirect('event_detail', slug=slug)
    
    # Check if already reviewed
    if Review.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, 'You have already reviewed this event.')
        return redirect('event_detail', slug=slug)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.event = event
            review.save()
            
            messages.success(request, 'Review added successfully!')
            return redirect('event_detail', slug=slug)
        else:
            messages.error(request, 'Please correct the errors in your review.')
    
    return redirect('event_detail', slug=slug)


@login_required
def toggle_favorite(request, slug):
    """Add/remove event from favorites"""
    event = get_object_or_404(Event, slug=slug)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        event=event
    )
    
    if not created:
        favorite.delete()
        message = 'Removed from favorites'
        is_favorited = False
    else:
        message = 'Added to favorites'
        is_favorited = True
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'message': message, 
            'is_favorited': is_favorited
        })
    
    messages.success(request, message)
    return redirect('event_detail', slug=slug)


def search_autocomplete(request):
    """AJAX autocomplete for search"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search events
    events = Event.objects.filter(
        Q(title__icontains=query) | Q(location__icontains=query),
        is_active=True
    ).select_related('city')[:5]
    
    # Search cities
    cities = City.objects.filter(name__icontains=query)[:3]
    
    results = []
    
    # Add cities to results
    for city in cities:
        results.append({
            'type': 'city',
            'name': city.name,
            'url': f'/events/?city={city.slug}'
        })
    
    # Add events to results
    for event in events:
        results.append({
            'type': 'event',
            'name': event.title,
            'location': event.location,
            'url': event.get_absolute_url()
        })
    
    return JsonResponse({'results': results})

def load_more_events(request):
    """AJAX endpoint for infinite scroll - load more events"""
    from django.core.paginator import Paginator
    
    page = int(request.GET.get('page', 1))
    per_page = 12
    
    # Get query parameters
    query_params = request.GET
    
    # Build queryset with filters
    queryset = Event.objects.filter(
        is_active=True,
        start_date__gte=datetime.now().date()
    ).select_related('city', 'host').prefetch_related('images', 'reviews')
    
    # Apply filters
    search_query = query_params.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(city__name__icontains=search_query) |
            Q(category__icontains=search_query)
        )
    
    location = query_params.get('location', '').strip()
    if location:
        queryset = queryset.filter(
            Q(city__name__icontains=location) |
            Q(location__icontains=location) |
            Q(city__state__icontains=location)
        )
    
    category = query_params.get('category', '').strip()
    if category and category != 'all':
        queryset = queryset.filter(category=category)
    
    city = query_params.get('city', '').strip()
    if city:
        queryset = queryset.filter(city__slug=city)
    
    date = query_params.get('date', '').strip()
    if date:
        try:
            event_date = datetime.strptime(date, '%Y-%m-%d').date()
            queryset = queryset.filter(
                start_date__lte=event_date,
                end_date__gte=event_date
            )
        except ValueError:
            pass
    
    # Sort
    sort = query_params.get('sort', '-created_at')
    if sort == 'popular':
        queryset = queryset.annotate(
            booking_count=Count('bookings')
        ).order_by('-booking_count')
    else:
        queryset = queryset.order_by(sort)
    
    # Paginate
    paginator = Paginator(queryset.distinct(), per_page)
    events_page = paginator.get_page(page)
    
    # Build JSON response
    events_data = []
    for event in events_page:
        image_url = event.images.first().image.url if event.images.first() else 'https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=500'
        
        events_data.append({
            'slug': event.slug,
            'title': event.title,
            'city': event.city.name,
            'state': event.city.state,
            'price': float(event.price),
            'image_url': image_url,
            'start_date': event.start_date.strftime('%b %d, %Y'),
            'end_date': event.end_date.strftime('%b %d, %Y'),
            'same_date': event.start_date == event.end_date,
            'average_rating': float(event.average_rating()) if event.average_rating() > 0 else 0,
            'detail_url': event.get_absolute_url()
        })
    
    return JsonResponse({
        'events': events_data,
        'has_next': events_page.has_next(),
        'current_page': page,
        'total_pages': paginator.num_pages
    })


def signup(request):
    """User registration with validation"""
    if request.user.is_authenticated:
        return redirect('event_list')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        is_host = request.POST.get('is_host') == 'on'
        
        # Validation
        errors = []
        
        # Username validation
        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        elif not username.replace('_', '').isalnum():
            errors.append('Username can only contain letters, numbers, and underscores.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already exists. Please choose another.')
        
        # Email validation
        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered. Please login instead.')
        
        # Password validation
        if not password1:
            errors.append('Password is required.')
        elif len(password1) < 8:
            errors.append('Password must be at least 8 characters long.')
        
        if password1 != password2:
            errors.append('Passwords do not match.')
        
        # If there are errors, show them
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'registration/signup.html', {
                'username': username,
                'email': email
            })
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            user.is_host = is_host
            user.save()
            
            # Log the user in
            login(request, user)
            
            if is_host:
                messages.success(request, f'Welcome {username}! Your host account has been created. Start creating events!')
            else:
                messages.success(request, f'Welcome {username}! Your account has been created. Start exploring events!')
            
            return redirect('event_list')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'registration/signup.html', {
                'username': username,
                'email': email
            })
    
    return render(request, 'registration/signup.html')


@login_required
def delete_event(request, slug):
    """Delete an event (soft delete by marking as inactive)"""
    event = get_object_or_404(Event, slug=slug, host=request.user)
    
    if request.method == 'POST':
        event.is_active = False
        event.save()
        messages.success(request, 'Event deleted successfully.')
        return redirect('my_events')
    
    return redirect('event_detail', slug=slug)


def events_by_city(request, city_slug):
    """Show events for a specific city"""
    city = get_object_or_404(City, slug=city_slug)
    
    events = Event.objects.filter(
        city=city,
        is_active=True,
        start_date__gte=datetime.now().date()
    ).select_related('host').prefetch_related('images', 'reviews')
    
    return render(request, 'events/event_list.html', {
        'events': events,
        'city': city,
        'categories': Event.CATEGORY_CHOICES
    })


@login_required
def profile_view(request):
    """User profile page"""
    user = request.user
    
    # Get user's bookings
    bookings = Booking.objects.filter(user=user).select_related('event').order_by('-booking_date')[:5]
    
    # Get user's favorites
    favorites = Favorite.objects.filter(user=user).select_related('event').order_by('-created_at')[:6]
    
    # Get user's reviews
    reviews = Review.objects.filter(user=user).select_related('event').order_by('-created_at')[:5]
    
    # Stats for hosts
    if user.is_host:
        hosted_events = Event.objects.filter(host=user)
        total_bookings = Booking.objects.filter(event__host=user).count()
        total_revenue = Booking.objects.filter(
            event__host=user,
            is_paid=True
        ).aggregate(total=Count('id'))['total'] or 0
    else:
        hosted_events = None
        total_bookings = 0
        total_revenue = 0
    
    context = {
        'user': user,
        'bookings': bookings,
        'favorites': favorites,
        'reviews': reviews,
        'hosted_events': hosted_events,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'events/profile.html', context)


@login_required
def settings_view(request):
    """User settings page"""
    user = request.user
    
    if request.method == 'POST':
        # Update basic info
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.bio = request.POST.get('bio', '')
        
        # Handle profile image upload
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        
        # Handle password change
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if current_password and new_password:
            if user.check_password(current_password):
                if new_password == confirm_password:
                    if len(new_password) >= 8:
                        user.set_password(new_password)
                        messages.success(request, 'Password updated successfully! Please login again.')
                        user.save()
                        return redirect('login')
                    else:
                        messages.error(request, 'Password must be at least 8 characters long.')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Current password is incorrect.')
        
        try:
            user.save()
            messages.success(request, 'Settings updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating settings: {str(e)}')
        
        return redirect('settings')
    
    return render(request, 'events/settings.html', {'user': user})


@login_required
def delete_account(request):
    """Delete user account"""
    if request.method == 'POST':
        password = request.POST.get('confirm_password', '')
        
        # Verify password before deletion
        if not request.user.check_password(password):
            messages.error(request, 'Incorrect password. Account not deleted.')
            return redirect('settings')
        
        # Get user info before deletion
        username = request.user.username
        user = request.user
        
        try:
            # If user is a host, handle their events
            if user.is_host:
                # Deactivate all hosted events instead of deleting
                Event.objects.filter(host=user).update(is_active=False)
            
            # Cancel all upcoming bookings
            from django.utils import timezone
            upcoming_bookings = Booking.objects.filter(
                user=user,
                event_date__gte=timezone.now().date(),
                status__in=['pending', 'confirmed']
            )
            
            for booking in upcoming_bookings:
                # Return tickets to event
                booking.event.available_tickets += booking.tickets
                booking.event.save()
                # Mark as cancelled
                booking.status = 'cancelled'
                booking.save()
            
            # Logout first
            from django.contrib.auth import logout
            logout(request)
            
            # Delete the account
            user.delete()
            
            messages.success(request, f'Account "{username}" has been permanently deleted. We\'re sorry to see you go!')
            return redirect('event_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting account: {str(e)}')
            return redirect('settings')
    
    # GET request - show confirmation page
    return render(request, 'events/delete_account_confirm.html')


def logout_view(request):
    """Custom logout view - requires POST for security"""
    from django.contrib.auth import logout
    
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('event_list')
    
    # If GET request, show a confirmation page or redirect
    return redirect('event_list')