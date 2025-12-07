from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, City, Event, EventImage, Booking, Review, Favorite


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_host', 'is_staff']
    list_filter = ['is_host', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Host Information', {'fields': ('is_host', 'phone', 'profile_image', 'bio')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('is_host', 'phone')}),
    )
    search_fields = ['username', 'email', 'first_name', 'last_name']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'country', 'is_featured', 'event_count_display']
    list_filter = ['is_featured', 'country', 'state']
    search_fields = ['name', 'state', 'country']
    prepopulated_fields = {'slug': ('name',)}
    
    def event_count_display(self, obj):
        count = obj.event_count()
        return format_html('<strong>{}</strong> events', count)
    event_count_display.short_description = 'Events'


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 1
    fields = ['image', 'is_primary', 'order']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'host', 'city', 'category', 'start_date', 'price', 
        'capacity', 'available_tickets', 'is_active', 'is_featured'
    ]
    list_filter = [
        'category', 'is_active', 'is_featured', 'start_date', 'city'
    ]
    search_fields = ['title', 'description', 'location', 'host__username']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    inlines = [EventImageInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'host', 'description', 'category')
        }),
        ('Location', {
            'fields': ('city', 'location')
        }),
        ('Date & Time', {
            'fields': ('start_date', 'end_date', 'start_time')
        }),
        ('Pricing & Capacity', {
            'fields': ('price', 'capacity', 'available_tickets')
        }),
        ('Additional Details', {
            'fields': ('included', 'things_to_know', 'cancellation_policy', 'age_restriction'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # New event
            obj.host = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ['event', 'is_primary', 'order', 'image_preview']
    list_filter = ['is_primary', 'event__category']
    search_fields = ['event__title']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="100" height="75" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'event', 'event_date', 'tickets', 
        'total_price', 'status', 'is_paid', 'booking_date'
    ]
    list_filter = ['status', 'is_paid', 'booking_date', 'event_date']
    search_fields = ['user__username', 'event__title', 'payment_id']
    date_hierarchy = 'booking_date'
    readonly_fields = ['booking_date', 'updated_at']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'event', 'tickets', 'event_date')
        }),
        ('Payment', {
            'fields': ('total_price', 'is_paid', 'payment_id')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('booking_date', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_completed', 'cancel_bookings']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(is_paid=True)
        self.message_user(request, f'{updated} booking(s) marked as paid.')
    mark_as_paid.short_description = 'Mark selected bookings as paid'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} booking(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected bookings as completed'
    
    def cancel_bookings(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} booking(s) cancelled.')
    cancel_bookings.short_description = 'Cancel selected bookings'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'rating', 'created_at', 'comment_preview']
    list_filter = ['rating', 'created_at', 'event__category']
    search_fields = ['user__username', 'event__title', 'comment']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'created_at']
    list_filter = ['created_at', 'event__category']
    search_fields = ['user__username', 'event__title']
    date_hierarchy = 'created_at'


# Customize admin site headers
admin.site.site_header = 'EventSpace Administration'
admin.site.site_title = 'EventSpace Admin'
admin.site.index_title = 'Welcome to EventSpace Administration'