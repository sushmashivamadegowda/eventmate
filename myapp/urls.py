from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .health_check import health_check, readiness_check, liveness_check, metrics

urlpatterns = [
    # Home and Event Listing
    path('', views.EventListView.as_view(), name='event_list'),
    path('events/', views.EventListView.as_view(), name='event_list_alt'),

    # Search
    path('search/autocomplete/', views.search_autocomplete, name='search_autocomplete'), 

    # Event Detail
    path('event/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),

    # Event Management (Hosts)
    path('create/', views.create_event, name='create_event'),
    path('event/<slug:slug>/edit/', views.update_event, name='update_event'),
    path('event/<slug:slug>/delete/', views.delete_event, name='delete_event'),
    path('my-events/', views.my_events, name='my_events'),

    # Bookings
    path('event/<slug:slug>/book/', views.create_booking, name='create_booking'),
    path('booking/<int:booking_id>/confirm/', views.booking_confirm, name='booking_confirm'),
    path('booking/<int:booking_id>/payment/', views.process_payment, name='process_payment'),
    path('booking/<int:booking_id>/payment/success/', views.payment_success, name='payment_success'),
    path('booking/<int:booking_id>/payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),

    # Reviews
    path('event/<slug:slug>/review/', views.add_review, name='add_review'),

    # Favorites
    path('event/<slug:slug>/favorite/', views.toggle_favorite, name='toggle_favorite'),

    # City Filter
    path('city/<slug:city_slug>/', views.events_by_city, name='events_by_city'),

    # User Profile & Settings
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
    
    #singup-logout
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/logout/', views.logout_view, name='logout'),
    
    # Authentication - Django built-in views
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html'), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'), name='password_change_done'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    
    # Health Check and Monitoring
    path('health/', health_check, name='health_check'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/live/', liveness_check, name='liveness_check'),
    path('metrics/', metrics, name='metrics'),
]

