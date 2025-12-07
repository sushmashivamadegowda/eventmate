from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse


class User(AbstractUser):
    """Extended User model with host capabilities"""
    is_host = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    
    def __str__(self):
        return self.username


class City(models.Model):
    """Cities where events are hosted"""
    name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='USA')
    image = models.ImageField(upload_to='cities/')
    slug = models.SlugField(unique=True, blank=True)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Cities'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def event_count(self):
        return self.events.filter(is_active=True).count()
    
    def __str__(self):
        return f"{self.name}, {self.state}"


class Event(models.Model):
    """Main Event model"""
    CATEGORY_CHOICES = [
        ('all', 'All Events'),
        ('music', 'Music'),
        ('sports', 'Sports'),
        ('arts', 'Arts'),
        ('food', 'Food & Drink'),
        ('business', 'Business'),
        ('tech', 'Technology'),
        ('wellness', 'Wellness'),
    ]
    
    # Basic Information
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_events')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Location
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, related_name='events')
    location = models.CharField(max_length=200, help_text="Venue name or address")
    
    # Date and Time
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    
    # Pricing and Capacity
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    available_tickets = models.IntegerField()
    
    # Additional Details
    included = models.TextField(blank=True, help_text="What's included in the ticket")
    things_to_know = models.TextField(blank=True)
    cancellation_policy = models.TextField(blank=True)
    age_restriction = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['start_date', 'is_active']),
            models.Index(fields=['city', 'is_active']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.available_tickets:
            self.available_tickets = self.capacity
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})
    
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(r.rating for r in reviews) / len(reviews)
        return 0
    
    def review_count(self):
        return self.reviews.count()
    
    def tickets_remaining(self):
        return self.available_tickets
    
    def is_sold_out(self):
        return self.available_tickets <= 0
    
    def __str__(self):
        return self.title


class EventImage(models.Model):
    """Multiple images for events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='events/')
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-is_primary', 'order']
    
    def __str__(self):
        return f"Image for {self.event.title}"


class Booking(models.Model):
    """Event bookings"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking Details
    tickets = models.IntegerField(validators=[MinValueValidator(1)])
    event_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    booking_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Payment
    payment_id = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-booking_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.tickets} tickets)"


class Review(models.Model):
    """Event reviews and ratings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', null=True, blank=True)
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'event']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.rating}★)"


class Favorite(models.Model):
    """User favorites/wishlist"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'event']
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"